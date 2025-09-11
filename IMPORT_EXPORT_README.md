# Import/Export Functionality

This document describes the import/export functionality that has been added to the Kemco Portal Django application.

## Overview

The application now supports importing and exporting data through the Django admin interface using the `django-import-export` package. This allows you to:

- Export data from any model to CSV, Excel, or JSON formats
- Import data from CSV, Excel, or JSON files
- Bulk operations for large datasets
- Data validation and error handling

## Features

### ✅ **Available for All Models**

**D365 App Models:**
- D365Job - Job management
- D365Heater - Heater specifications
- D365Tank - Tank specifications  
- D365Pump - Pump specifications
- D365GeneratedItem - Generated BOM items
- All reference data models (materials, sizes, types, etc.)

**Dynamics Search App Models:**
- Part - Parts inventory with search capabilities

### ✅ **Export Formats**
- CSV (default)
- Excel (.xlsx)
- JSON

### ✅ **Admin Interface Features**
- Import/Export buttons on each model's admin page
- Bulk import with validation
- Export with filtering and search
- Progress tracking for large operations
- Error reporting and validation

## Usage

### 1. **Admin Interface**

1. Navigate to `/admin/` in your browser
2. Select any model (e.g., "Parts" or "D365 jobs")
3. Use the "Import" or "Export" buttons at the top
4. Follow the on-screen instructions

### 2. **Management Commands**

#### Export Parts Data
```bash
# Export all parts to CSV
python manage.py export_parts_data

# Export limited number of parts
python manage.py export_parts_data --limit 100

# Export to Excel format
python manage.py export_parts_data --format xlsx

# Export to JSON format
python manage.py export_parts_data --format json
```

#### Export D365 Data
```bash
# Export all D365 data to CSV
python manage.py export_sample_data

# Export to Excel format
python manage.py export_sample_data --format xlsx

# Export to JSON format
python manage.py export_sample_data --format json
```

### 3. **File Locations**

Exported files are saved to the `exports/` directory:
```
exports/
├── parts.csv                    # Parts data
├── d365_jobs.csv               # D365 jobs
├── d365_heaters.csv            # D365 heaters
├── d365_tanks.csv              # D365 tanks
├── d365_pumps.csv              # D365 pumps
└── d365_generated_items.csv    # Generated BOM items
```

## Configuration

### Settings

The following settings have been added to `settings.py`:

```python
# Import/Export Configuration
IMPORT_EXPORT_USE_TRANSACTIONS = True
IMPORT_EXPORT_SKIP_ADMIN_LOG = False
IMPORT_EXPORT_CHUNK_SIZE = 1000
```

### Resource Classes

Each model has a corresponding resource class that defines:
- Which fields to include in import/export
- Field validation rules
- Data transformation logic
- Import/export order

**Location:** `d365/resources.py` and `dynamics_search/resources.py`

## Data Validation

### Import Validation
- Required fields are validated
- Data types are checked
- Unique constraints are enforced
- Foreign key relationships are validated

### Export Features
- All fields are included by default
- Data is properly formatted
- Relationships are resolved to readable values
- Timestamps are included

## Error Handling

### Import Errors
- Validation errors are displayed with specific field information
- Duplicate records are handled according to configuration
- Missing required fields are clearly identified
- Data type mismatches are reported

### Export Errors
- Large datasets are processed in chunks
- Memory usage is optimized
- Progress is tracked for long operations

## Examples

### Exporting Parts Data

1. **Via Admin Interface:**
   - Go to `/admin/dynamics_search/part/`
   - Click "Export" button
   - Select format (CSV/Excel/JSON)
   - Download the file

2. **Via Command Line:**
   ```bash
   python manage.py export_parts_data --format xlsx --limit 50
   ```

### Importing New Parts

1. **Prepare CSV File:**
   ```csv
   item_number,description,size
   KMC-1234-VAL-1,Test Valve 1",1"
   KMC-5678-PIP-2,Test Pipe 2",2"
   ```

2. **Import via Admin:**
   - Go to `/admin/dynamics_search/part/`
   - Click "Import" button
   - Upload the CSV file
   - Review and confirm import

### Exporting D365 Jobs

1. **Via Admin Interface:**
   - Go to `/admin/d365/d365job/`
   - Use filters to select specific jobs
   - Click "Export" button
   - Download filtered data

2. **Via Command Line:**
   ```bash
   python manage.py export_sample_data --format csv
   ```

## Troubleshooting

### Common Issues

1. **Import Validation Errors:**
   - Check that all required fields are present
   - Verify data types match expected format
   - Ensure unique constraints are satisfied

2. **Export Memory Issues:**
   - Use the `--limit` parameter for large datasets
   - Consider using CSV format for very large exports
   - Process data in smaller chunks

3. **File Format Issues:**
   - Ensure CSV files use UTF-8 encoding
   - Check that Excel files are not password protected
   - Verify JSON files are properly formatted

### Performance Tips

1. **Large Imports:**
   - Use CSV format for better performance
   - Import during off-peak hours
   - Consider splitting large files into smaller chunks

2. **Large Exports:**
   - Use filters to limit exported data
   - Consider using the command line for very large exports
   - Monitor memory usage during export

## Security Considerations

- Import/export functionality is only available to admin users
- All operations are logged in the Django admin
- File uploads are validated for security
- Data is processed in transactions for consistency

## Support

For issues or questions about the import/export functionality:

1. Check the Django admin logs for error details
2. Review the exported data format for reference
3. Test with small datasets first
4. Contact the development team for assistance

## Future Enhancements

Potential improvements for the import/export system:

- Custom field mapping for imports
- Scheduled exports
- Email notifications for completed operations
- Advanced filtering options
- Data transformation rules
- Integration with external systems
