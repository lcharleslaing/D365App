#!/usr/bin/env python
"""
Test script for Excel sync functionality.
This script demonstrates how to use the sync_from_excel management command.
"""

import os
import sys
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kemco_portal.settings')
django.setup()

def test_dry_run():
    """Test the sync command in dry-run mode"""
    print("Testing Excel sync in dry-run mode...")
    print("=" * 50)
    
    try:
        call_command(
            'sync_from_excel',
            excel_path='path/to/d365_parts.xlsx',
            csv_path='test_parts_export.csv',
            wait_time=5,  # Short wait for testing
            dry_run=True,
            verbose=True
        )
        print("Dry run test completed successfully!")
        
    except Exception as e:
        print(f"Dry run test failed: {e}")
        print("This is expected if the Excel file doesn't exist yet.")

def test_with_sample_data():
    """Test with sample CSV data"""
    print("\nTesting with sample CSV data...")
    print("=" * 50)
    
    # Create a sample CSV file for testing
    import pandas as pd
    
    sample_data = {
        'item_number': ['TEST001', 'TEST002', 'TEST003'],
        'description': ['Test Part 1', 'Test Part 2', 'Test Part 3'],
        'size': ['10mm', '20mm', '30mm'],
        'product_group_id': ['GROUP1', 'GROUP2', 'GROUP3'],
        'vendor_name': ['Test Vendor 1', 'Test Vendor 2', 'Test Vendor 3']
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv('sample_parts.csv', index=False)
    print("Created sample CSV file: sample_parts.csv")
    
    try:
        call_command(
            'sync_from_excel',
            excel_path='sample_parts.csv',  # Use CSV as input for testing
            csv_path='test_output.csv',
            wait_time=1,
            dry_run=True,
            verbose=True
        )
        print("Sample data test completed successfully!")
        
    except Exception as e:
        print(f"Sample data test failed: {e}")

if __name__ == '__main__':
    print("Excel Sync Test Script")
    print("=" * 50)
    
    # Test 1: Dry run with non-existent Excel file
    test_dry_run()
    
    # Test 2: Test with sample data
    test_with_sample_data()
    
    print("\nTest script completed!")
    print("\nTo run the actual sync command:")
    print("python manage.py sync_from_excel --excel-path 'your_excel_file.xlsx' --dry-run")
