from django.core.management.base import BaseCommand
from dynamics_search.models import Part
from dynamics_search.resources import PartResource
import os


class Command(BaseCommand):
    help = 'Export parts data to CSV files for testing import/export functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='exports',
            help='Directory to save exported files (default: exports)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'xlsx', 'json'],
            default='csv',
            help='Export format (default: csv)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of records to export'
        )
    
    def handle(self, *args, **options):
        output_dir = options['output_dir']
        export_format = options['format']
        limit = options.get('limit')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Get parts data
            queryset = Part.objects.all()
            
            if limit:
                queryset = queryset[:limit]
            
            if queryset.exists():
                # Export data
                resource = PartResource()
                dataset = resource.export(queryset)
                
                # Save to file
                file_path = os.path.join(output_dir, f"parts.{export_format}")
                
                with open(file_path, 'wb') as f:
                    if export_format == 'csv':
                        f.write(dataset.csv.encode('utf-8'))
                    elif export_format == 'xlsx':
                        f.write(dataset.xlsx)
                    elif export_format == 'json':
                        f.write(dataset.json.encode('utf-8'))
                
                self.stdout.write(
                    self.style.SUCCESS(f"Exported {queryset.count()} parts to {file_path}")
                )
                
                # Show sample of exported data
                self.stdout.write("\nSample exported data:")
                sample_data = queryset[:5]
                for part in sample_data:
                    self.stdout.write(f"  - {part.item_number}: {part.description[:50]}...")
                
            else:
                self.stdout.write(
                    self.style.WARNING("No parts found to export. Run 'python manage.py seed_parts' first.")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error exporting parts: {str(e)}")
            )
