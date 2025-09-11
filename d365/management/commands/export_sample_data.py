from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from d365.models import D365Job, D365Heater, D365Tank, D365Pump, D365GeneratedItem
from d365.resources import (
    D365JobResource, D365HeaterResource, D365TankResource, 
    D365PumpResource, D365GeneratedItemResource
)
import os


class Command(BaseCommand):
    help = 'Export sample data to CSV files for testing import/export functionality'
    
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
    
    def handle(self, *args, **options):
        output_dir = options['output_dir']
        export_format = options['format']
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Define resources and their corresponding models
        resources = [
            (D365JobResource(), D365Job, 'd365_jobs'),
            (D365HeaterResource(), D365Heater, 'd365_heaters'),
            (D365TankResource(), D365Tank, 'd365_tanks'),
            (D365PumpResource(), D365Pump, 'd365_pumps'),
            (D365GeneratedItemResource(), D365GeneratedItem, 'd365_generated_items'),
        ]
        
        exported_files = []
        
        for resource, model, filename in resources:
            try:
                # Get all objects from the model
                queryset = model.objects.all()
                
                if queryset.exists():
                    # Export data
                    dataset = resource.export(queryset)
                    
                    # Save to file
                    file_path = os.path.join(output_dir, f"{filename}.{export_format}")
                    
                    with open(file_path, 'wb') as f:
                        if export_format == 'csv':
                            f.write(dataset.csv.encode('utf-8'))
                        elif export_format == 'xlsx':
                            f.write(dataset.xlsx)
                        elif export_format == 'json':
                            f.write(dataset.json.encode('utf-8'))
                    
                    exported_files.append(file_path)
                    self.stdout.write(
                        self.style.SUCCESS(f"Exported {queryset.count()} {model.__name__} records to {file_path}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"No {model.__name__} records found to export")
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error exporting {model.__name__}: {str(e)}")
                )
        
        if exported_files:
            self.stdout.write(
                self.style.SUCCESS(f"\nSuccessfully exported {len(exported_files)} files to {output_dir}/")
            )
            self.stdout.write("Files exported:")
            for file_path in exported_files:
                self.stdout.write(f"  - {file_path}")
        else:
            self.stdout.write(
                self.style.WARNING("No data was exported. Make sure you have some data in your database.")
            )
