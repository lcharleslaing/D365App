#!/usr/bin/env python
"""
Setup script for Excel sync functionality.
This script helps configure the Excel sync feature for the Kemco D365 Import App.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Setting up: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Error:", e.stderr)
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description} exists: {file_path}")
        return True
    else:
        print(f"❌ {description} missing: {file_path}")
        return False

def main():
    print("🚀 Setting up Excel Sync for Kemco D365 Import App")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found. Please run this script from the Django project root.")
        sys.exit(1)
    
    # Step 1: Install Python dependencies
    print("\n📦 Installing Python dependencies...")
    dependencies = [
        'pywin32',
        'pandas', 
        'openpyxl',
        'celery',
        'redis',  # For Celery broker
        'django-celery-beat'  # For scheduled tasks
    ]
    
    for dep in dependencies:
        success = run_command(f"pip install {dep}", f"Installing {dep}")
        if not success:
            print(f"⚠️  Warning: Failed to install {dep}")
    
    # Step 2: Create sample Excel file
    print("\n📊 Creating sample Excel file...")
    sample_script = """
import pandas as pd
import os

# Create sample data
sample_data = {
    'item_number': ['SAMPLE001', 'SAMPLE002', 'SAMPLE003', 'SAMPLE004'],
    'description': ['Sample Part 1', 'Sample Part 2', 'Sample Part 3', 'Sample Part 4'],
    'size': ['10mm', '20mm', '30mm', '40mm'],
    'product_group_id': ['GROUP1', 'GROUP2', 'GROUP3', 'GROUP4'],
    'vendor_name': ['Sample Vendor 1', 'Sample Vendor 2', 'Sample Vendor 3', 'Sample Vendor 4'],
    'unit_cost': [10.50, 25.75, 35.00, 45.25],
    'vendor_product_number': ['V001', 'V002', 'V003', 'V004']
}

# Create DataFrame
df = pd.DataFrame(sample_data)

# Create the directory if it doesn't exist
os.makedirs('path/to', exist_ok=True)

# Save as Excel file
excel_path = 'path/to/d365_parts.xlsx'
df.to_excel(excel_path, index=False)

print(f"Sample Excel file created: {excel_path}")
print(f"Contains {len(df)} sample records")
"""
    
    with open('temp_create_sample.py', 'w') as f:
        f.write(sample_script)
    
    run_command('python temp_create_sample.py', 'Creating sample Excel file')
    os.remove('temp_create_sample.py')
    
    # Step 3: Test management command
    print("\n🧪 Testing management command...")
    run_command('python manage.py sync_from_excel --dry-run', 'Testing sync command (dry run)')
    
    # Step 4: Check file structure
    print("\n📁 Checking file structure...")
    required_files = [
        'dynamics_search/management/commands/sync_from_excel.py',
        'dynamics_search/tasks.py',
        'kemco_portal/celery.py',
        'celery_beat_schedule.py',
        'requirements_excel_sync.txt',
        'EXCEL_SYNC_README.md'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if not check_file_exists(file_path, f"Required file"):
            all_files_exist = False
    
    # Step 5: Database migration check
    print("\n🗄️  Checking database migrations...")
    run_command('python manage.py makemigrations', 'Creating migrations')
    run_command('python manage.py migrate', 'Applying migrations')
    
    # Step 6: Test search functionality
    print("\n🔍 Testing search functionality...")
    run_command('python manage.py runserver --noreload &', 'Starting Django server (background)')
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    if all_files_exist:
        print("✅ All required files are present")
    else:
        print("⚠️  Some files may be missing - check the list above")
    
    print("\n📋 Next Steps:")
    print("1. Configure your Excel file path in the management command")
    print("2. Set up Redis server for Celery (if using scheduled tasks)")
    print("3. Test the sync command with your actual Excel file")
    print("4. Set up Celery Beat for automatic syncing")
    
    print("\n🔧 Manual Configuration:")
    print("- Edit 'dynamics_search/management/commands/sync_from_excel.py'")
    print("- Update the Excel file path (default: 'path/to/d365_parts.xlsx')")
    print("- Configure Redis in 'kemco_portal/settings.py'")
    
    print("\n📚 Documentation:")
    print("- Read 'EXCEL_SYNC_README.md' for detailed instructions")
    print("- Check 'requirements_excel_sync.txt' for dependencies")
    
    print("\n🚀 Ready to use!")
    print("Run: python manage.py sync_from_excel --help")

if __name__ == "__main__":
    main()
