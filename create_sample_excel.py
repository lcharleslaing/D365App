#!/usr/bin/env python
"""
Create a sample Excel file for testing the sync command.
"""

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
print("\nSample data:")
print(df.head())
