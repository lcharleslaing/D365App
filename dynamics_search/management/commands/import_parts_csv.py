from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from dynamics_search.models import Part
from dynamics_search.resources import PartResource
import os
import csv


class Command(BaseCommand):
    help = 'Import parts data from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Skip rows with errors and continue importing'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of rows to process in each batch (default: 100)'
        )
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        skip_errors = options['skip_errors']
        batch_size = options['batch_size']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f"CSV file not found: {csv_file}")
            )
            return
        
        # Create resource instance
        resource = PartResource()
        
        # Read and process CSV file
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            file_content = None
            
            for encoding in encodings:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        file_content = f.read()
                    self.stdout.write(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                self.stdout.write(
                    self.style.ERROR(f"Could not read file with any supported encoding. Tried: {', '.join(encodings)}")
                )
                return
            
            # Process the file content
            from io import StringIO
            f = StringIO(file_content)
            
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            # Read CSV
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Map CSV columns to model fields
            field_mapping = {
                'Item': 'item_number',
                'ItemNumber': 'item_number', 
                'ProductDescription': 'description',
                'ProductGroupId': 'product_group_id',
                'UnitCost': 'unit_cost',
                'UnitCostDate': 'unit_cost_date',
                'VendorName': 'vendor_name',
                'VendorProductNumber': 'vendor_product_number',
                'VendorProductDescription': 'vendor_product_description',
                'VendorPhone': 'vendor_phone'
            }
            
            imported_count = 0
            error_count = 0
            skipped_count = 0
            
            self.stdout.write(f"Processing CSV file: {csv_file}")
            self.stdout.write(f"Delimiter detected: '{delimiter}'")
            self.stdout.write(f"Dry run: {dry_run}")
            self.stdout.write("-" * 50)
            
            batch = []
            for row_num, row in enumerate(reader, 1):
                try:
                    # Map CSV fields to model fields
                    mapped_row = {}
                    for csv_field, model_field in field_mapping.items():
                        if csv_field in row:
                            mapped_row[model_field] = row[csv_field]
                    
                    # Skip empty rows
                    if not mapped_row.get('item_number'):
                        skipped_count += 1
                        continue
                    
                    if dry_run:
                        self.stdout.write(f"Row {row_num}: {mapped_row['item_number']} - {mapped_row.get('description', 'No description')[:50]}")
                    else:
                        batch.append(mapped_row)
                        
                        # Process batch when it reaches batch_size
                        if len(batch) >= batch_size:
                            # Create a dataset from the batch
                            from tablib import Dataset
                            dataset = Dataset()
                            # Remove duplicate item_number from headers
                            unique_headers = []
                            for field in field_mapping.values():
                                if field not in unique_headers:
                                    unique_headers.append(field)
                            dataset.headers = unique_headers
                            for row_data in batch:
                                dataset.append([row_data.get(field, '') for field in unique_headers])
                            
                            result = resource.import_data(dataset, dry_run=False)
                            if result.has_errors():
                                self.stdout.write(
                                    self.style.WARNING(f"Errors in batch starting at row {row_num - batch_size + 1}:")
                                )
                                for error in result.row_errors():
                                    self.stdout.write(f"  Row {error[0]}: {error[1]}")
                                    error_count += 1
                            else:
                                imported_count += len(batch)
                            
                            batch = []
                    
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(
                            self.style.WARNING(f"Error processing row {row_num}: {str(e)}")
                        )
                        continue
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing row {row_num}: {str(e)}")
                        )
                        if not dry_run:
                            break
            
            # Process remaining batch
            if not dry_run and batch:
                # Create a dataset from the batch
                from tablib import Dataset
                dataset = Dataset()
                # Remove duplicate item_number from headers
                unique_headers = []
                for field in field_mapping.values():
                    if field not in unique_headers:
                        unique_headers.append(field)
                dataset.headers = unique_headers
                for row_data in batch:
                    dataset.append([row_data.get(field, '') for field in unique_headers])
                
                result = resource.import_data(dataset, dry_run=False)
                if result.has_errors():
                    self.stdout.write(
                        self.style.WARNING(f"Errors in final batch:")
                    )
                    for error in result.row_errors():
                        self.stdout.write(f"  Row {error[0]}: {error[1]}")
                        error_count += 1
                else:
                    imported_count += len(batch)
            
            # Summary
            self.stdout.write("-" * 50)
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"Dry run completed. Would import {row_num - skipped_count} rows")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Import completed!")
                )
                self.stdout.write(f"  Imported: {imported_count} parts")
                self.stdout.write(f"  Errors: {error_count} rows")
                self.stdout.write(f"  Skipped: {skipped_count} empty rows")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error reading CSV file: {str(e)}")
            )
