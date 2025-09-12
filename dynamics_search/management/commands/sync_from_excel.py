import os
import sys
import time
import hashlib
import logging
import pandas as pd
from datetime import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from dynamics_search.models import Part

# Configure logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync parts data from Excel file with D365 refresh and CSV export'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--excel-path',
            type=str,
            default='path/to/d365_parts.xlsx',
            help='Path to the Excel file (default: path/to/d365_parts.xlsx)'
        )
        parser.add_argument(
            '--csv-path',
            type=str,
            default='parts_export.csv',
            help='Path for CSV export (default: parts_export.csv)'
        )
        parser.add_argument(
            '--wait-time',
            type=int,
            default=30,
            help='Wait time in seconds for Excel refresh (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        excel_path = options['excel_path']
        csv_path = options['csv_path']
        wait_time = options['wait_time']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if verbose:
            logging.basicConfig(level=logging.INFO)
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting Excel sync process...')
        )
        self.stdout.write(f'Excel file: {excel_path}')
        self.stdout.write(f'CSV output: {csv_path}')
        self.stdout.write(f'Wait time: {wait_time} seconds')
        self.stdout.write(f'Dry run: {dry_run}')
        
        try:
            # Step 1: Open Excel and refresh data
            self.stdout.write('Step 1: Opening Excel file and refreshing data...')
            self.refresh_excel_data(excel_path, wait_time)
            
            # Step 2: Export to CSV
            self.stdout.write('Step 2: Exporting to CSV...')
            self.export_excel_to_csv(excel_path, csv_path)
            
            # Step 3: Process CSV data
            self.stdout.write('Step 3: Processing CSV data...')
            df = self.load_csv_data(csv_path)
            
            # Step 4: Compare and sync with database
            self.stdout.write('Step 4: Syncing with database...')
            if not dry_run:
                self.sync_database(df, verbose)
            else:
                self.stdout.write(self.style.WARNING('DRY RUN: No database changes made'))
                self.analyze_changes(df, verbose)
            
            self.stdout.write(
                self.style.SUCCESS('Excel sync process completed successfully!')
            )
            
        except Exception as e:
            logger.error(f'Excel sync failed: {str(e)}')
            raise CommandError(f'Sync failed: {str(e)}')
    
    def refresh_excel_data(self, excel_path, wait_time):
        """Open Excel file and refresh data from D365"""
        try:
            import win32com.client as win32
            
            # Check if Excel file exists
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f'Excel file not found: {excel_path}')
            
            self.stdout.write(f'Opening Excel file: {excel_path}')
            
            # Start Excel application
            excel_app = win32.Dispatch("Excel.Application")
            excel_app.Visible = False  # Run in background
            excel_app.DisplayAlerts = False  # Disable alerts
            
            try:
                # Open the workbook
                workbook = excel_app.Workbooks.Open(os.path.abspath(excel_path))
                
                self.stdout.write('Refreshing all data connections...')
                # Refresh all data connections
                workbook.RefreshAll()
                
                # Wait for refresh to complete
                self.stdout.write(f'Waiting {wait_time} seconds for data refresh...')
                time.sleep(wait_time)
                
                # Save the workbook
                workbook.Save()
                self.stdout.write('Excel file saved successfully')
                
            finally:
                # Close workbook and Excel
                workbook.Close()
                excel_app.Quit()
                
        except ImportError:
            raise CommandError(
                'pywin32 is required for Excel operations. Install with: pip install pywin32'
            )
        except Exception as e:
            raise CommandError(f'Excel refresh failed: {str(e)}')
    
    def export_excel_to_csv(self, excel_path, csv_path):
        """Export Excel data to CSV using pandas"""
        try:
            self.stdout.write(f'Reading Excel file: {excel_path}')
            
            # Read Excel file
            df = pd.read_excel(excel_path)
            
            # Clean column names (remove spaces, special characters)
            df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
            
            self.stdout.write(f'Found {len(df)} rows in Excel file')
            
            # Save as CSV
            df.to_csv(csv_path, index=False)
            self.stdout.write(f'CSV exported successfully: {csv_path}')
            
        except Exception as e:
            raise CommandError(f'CSV export failed: {str(e)}')
    
    def load_csv_data(self, csv_path):
        """Load and validate CSV data"""
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f'CSV file not found: {csv_path}')
            
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['item_number', 'description', 'size']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f'Missing required columns: {missing_columns}')
            
            # Clean data
            df = df.dropna(subset=['item_number'])  # Remove rows without item_number
            df = df.fillna('')  # Fill NaN values with empty strings
            
            # Ensure item_number is string
            df['item_number'] = df['item_number'].astype(str)
            
            self.stdout.write(f'Loaded {len(df)} valid rows from CSV')
            return df
            
        except Exception as e:
            raise CommandError(f'CSV loading failed: {str(e)}')
    
    def generate_hash(self, item_number, description, size):
        """Generate MD5 hash for change detection"""
        content = f"{item_number}|{description}|{size}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def sync_database(self, df, verbose=False):
        """Sync CSV data with database"""
        try:
            with transaction.atomic():
                # Get all existing parts
                existing_parts = {
                    part.item_number: part 
                    for part in Part.objects.all()
                }
                
                # Track processed item numbers
                processed_item_numbers = set()
                
                # Lists for bulk operations
                parts_to_create = []
                parts_to_update = []
                
                self.stdout.write('Processing CSV rows...')
                
                for index, row in df.iterrows():
                    item_number = str(row['item_number']).strip()
                    description = str(row.get('description', '')).strip()
                    size = str(row.get('size', '')).strip()
                    
                    if not item_number:
                        continue
                    
                    processed_item_numbers.add(item_number)
                    
                    # Generate hash for this row
                    row_hash = self.generate_hash(item_number, description, size)
                    
                    if item_number in existing_parts:
                        # Check if part needs updating
                        existing_part = existing_parts[item_number]
                        existing_hash = self.generate_hash(
                            existing_part.item_number,
                            existing_part.description or '',
                            existing_part.size or ''
                        )
                        
                        if row_hash != existing_hash:
                            # Update existing part
                            existing_part.description = description
                            existing_part.size = size
                            existing_part.last_updated = timezone.now()
                            parts_to_update.append(existing_part)
                            
                            if verbose:
                                self.stdout.write(f'Updated: {item_number}')
                    else:
                        # Create new part
                        new_part = Part(
                            item_number=item_number,
                            description=description,
                            size=size,
                            last_updated=timezone.now()
                        )
                        parts_to_create.append(new_part)
                        
                        if verbose:
                            self.stdout.write(f'Created: {item_number}')
                
                # Bulk create new parts
                if parts_to_create:
                    Part.objects.bulk_create(parts_to_create, batch_size=1000)
                    self.stdout.write(f'Created {len(parts_to_create)} new parts')
                
                # Bulk update existing parts
                if parts_to_update:
                    Part.objects.bulk_update(
                        parts_to_update, 
                        ['description', 'size', 'last_updated'],
                        batch_size=1000
                    )
                    self.stdout.write(f'Updated {len(parts_to_update)} existing parts')
                
                # Mark missing parts as deleted
                missing_parts = set(existing_parts.keys()) - processed_item_numbers
                if missing_parts:
                    # Mark missing parts as deleted
                    missing_part_objects = [
                        existing_parts[item_num] for item_num in missing_parts
                    ]
                    for part in missing_part_objects:
                        part.is_deleted = True
                        part.last_updated = timezone.now()
                    
                    Part.objects.bulk_update(
                        missing_part_objects,
                        ['is_deleted', 'last_updated'],
                        batch_size=1000
                    )
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'Marked {len(missing_parts)} parts as deleted'
                        )
                    )
                    if verbose:
                        for item_num in list(missing_parts)[:10]:  # Show first 10
                            self.stdout.write(f'Marked as deleted: {item_num}')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Sync completed: {len(parts_to_create)} created, '
                        f'{len(parts_to_update)} updated, {len(missing_parts)} missing'
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Database sync failed: {str(e)}')
    
    def analyze_changes(self, df, verbose=False):
        """Analyze changes without making database modifications (dry run)"""
        try:
            existing_parts = {
                part.item_number: part 
                for part in Part.objects.all()
            }
            
            processed_item_numbers = set()
            would_create = 0
            would_update = 0
            
            for index, row in df.iterrows():
                item_number = str(row['item_number']).strip()
                description = str(row.get('description', '')).strip()
                size = str(row.get('size', '')).strip()
                
                if not item_number:
                    continue
                
                processed_item_numbers.add(item_number)
                row_hash = self.generate_hash(item_number, description, size)
                
                if item_number in existing_parts:
                    existing_part = existing_parts[item_number]
                    existing_hash = self.generate_hash(
                        existing_part.item_number,
                        existing_part.description or '',
                        existing_part.size or ''
                    )
                    
                    if row_hash != existing_hash:
                        would_update += 1
                        if verbose:
                            self.stdout.write(f'Would update: {item_number}')
                else:
                    would_create += 1
                    if verbose:
                        self.stdout.write(f'Would create: {item_number}')
            
            missing_parts = set(existing_parts.keys()) - processed_item_numbers
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Dry run analysis: {would_create} would be created, '
                    f'{would_update} would be updated, {len(missing_parts)} would be missing'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Dry run analysis failed: {str(e)}')
