from django.core.management.base import BaseCommand
from django.db import transaction
from dynamics_search.models import Part
import random


class Command(BaseCommand):
    help = 'Seed the database with sample parts data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of sample parts to create (default: 100)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing parts before seeding'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']
        
        if clear:
            self.stdout.write("Clearing existing parts...")
            Part.objects.all().delete()
        
        self.stdout.write(f"Creating {count} sample parts...")
        
        # Sample data
        part_types = [
            'Valve', 'Pipe', 'Fitting', 'Gasket', 'Bolt', 'Nut', 'Washer',
            'Hose', 'Coupling', 'Flange', 'Elbow', 'Tee', 'Reducer', 'Cap',
            'Plug', 'Union', 'Adapter', 'Filter', 'Strainer', 'Check Valve'
        ]
        
        materials = [
            'Steel', 'Stainless Steel', 'Brass', 'Copper', 'Aluminum',
            'PVC', 'HDPE', 'Cast Iron', 'Carbon Steel', 'Alloy Steel'
        ]
        
        sizes = [
            '1/4"', '1/2"', '3/4"', '1"', '1.25"', '1.5"', '2"', '2.5"',
            '3"', '4"', '6"', '8"', '10"', '12"', '16"', '20"', '24"'
        ]
        
        descriptions = [
            'High pressure', 'Low pressure', 'Standard', 'Heavy duty',
            'Light duty', 'Corrosion resistant', 'Temperature rated',
            'Food grade', 'Marine grade', 'Industrial grade'
        ]
        
        with transaction.atomic():
            parts_to_create = []
            
            for i in range(count):
                part_type = random.choice(part_types)
                material = random.choice(materials)
                size = random.choice(sizes)
                description_adj = random.choice(descriptions)
                
                # Generate item number
                item_number = f"KMC-{random.randint(1000, 9999)}-{part_type.upper()[:3]}-{size.replace('"', '')}"
                
                # Generate description
                description = f"{description_adj} {material} {part_type} {size} - {self.generate_description_details(part_type)}"
                
                part = Part(
                    item_number=item_number,
                    description=description,
                    size=size
                )
                parts_to_create.append(part)
            
            # Bulk create
            Part.objects.bulk_create(parts_to_create, batch_size=100)
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {count} sample parts!")
        )
    
    def generate_description_details(self, part_type):
        """Generate additional description details based on part type"""
        details = {
            'Valve': ['Gate valve', 'Ball valve', 'Check valve', 'Globe valve'],
            'Pipe': ['Schedule 40', 'Schedule 80', 'Seamless', 'Welded'],
            'Fitting': ['Threaded', 'Socket weld', 'Butt weld', 'Flanged'],
            'Gasket': ['Rubber', 'Cork', 'Metal', 'Spiral wound'],
            'Bolt': ['Hex head', 'Socket head', 'Carriage', 'Machine'],
            'Hose': ['Flexible', 'Reinforced', 'High pressure', 'Chemical resistant'],
        }
        
        return random.choice(details.get(part_type, ['Standard', 'Heavy duty', 'Industrial']))
