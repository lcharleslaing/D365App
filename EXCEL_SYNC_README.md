# Excel Sync Management Command

This document describes the Excel sync functionality for automatically syncing D365 parts data from Excel files to the Django database.

## Overview

The `sync_from_excel` management command provides automated synchronization between Excel files connected to D365 and the local Django database. It handles data refresh, change detection, and bulk database operations.

## Features

- **Excel Integration**: Uses pywin32 to open Excel files and refresh D365 data connections
- **Change Detection**: Uses MD5 hashing to detect changes in item_number, description, and size
- **Bulk Operations**: Efficient bulk create, update, and delete operations
- **Error Handling**: Comprehensive error handling for Excel crashes and network timeouts
- **Scheduling**: Support for Celery Beat scheduling (daily/hourly)
- **Dry Run**: Test mode to analyze changes without making database modifications

## Installation

1. Install required dependencies:
```bash
pip install -r requirements_excel_sync.txt
```

2. Run database migrations:
```bash
python manage.py migrate
```

## Usage

### Basic Usage

```bash
# Basic sync with default settings
python manage.py sync_from_excel

# Custom Excel file path
python manage.py sync_from_excel --excel-path "C:/path/to/your/d365_parts.xlsx"

# Custom CSV output path
python manage.py sync_from_excel --csv-path "custom_export.csv"

# Custom wait time for Excel refresh
python manage.py sync_from_excel --wait-time 60

# Dry run (no database changes)
python manage.py sync_from_excel --dry-run

# Verbose output
python manage.py sync_from_excel --verbose
```

### Command Options

- `--excel-path`: Path to the Excel file (default: 'path/to/d365_parts.xlsx')
- `--csv-path`: Path for CSV export (default: 'parts_export.csv')
- `--wait-time`: Wait time in seconds for Excel refresh (default: 30)
- `--dry-run`: Run without making database changes
- `--verbose`: Enable verbose output

## Scheduling

### Celery Beat (Recommended)

1. Install Celery and Celery Beat:
```bash
pip install celery celery-beat
```

2. Configure your Django settings to include Celery:
```python
# In settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'daily-excel-sync': {
        'task': 'dynamics_search.tasks.sync_excel_data',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM daily
    },
}

CELERY_TIMEZONE = 'UTC'
```

3. Start Celery Beat:
```bash
celery -A kemco_portal beat --loglevel=info
```

4. Start Celery Worker:
```bash
celery -A kemco_portal worker --loglevel=info
```

### Cron (Alternative)

Add to your crontab for daily execution at 3 AM:
```bash
# Edit crontab
crontab -e

# Add this line for daily sync at 3 AM
0 3 * * * cd /path/to/your/project && python manage.py sync_from_excel
```

For hourly execution:
```bash
# Every hour at minute 0
0 * * * * cd /path/to/your/project && python manage.py sync_from_excel --wait-time 15
```

## Process Flow

1. **Excel Refresh**: Opens the Excel file and calls `RefreshAll()` to update D365 data
2. **Wait Period**: Waits for the specified time (default 30 seconds) for refresh to complete
3. **CSV Export**: Exports the refreshed data to CSV using pandas
4. **Data Processing**: Loads and validates the CSV data
5. **Change Detection**: Compares each row's hash against existing database records
6. **Bulk Operations**:
   - Creates new parts for items not in database
   - Updates existing parts with changed data
   - Marks missing parts as deleted (`is_deleted=True`)

## Data Model Changes

The command adds an `is_deleted` field to the Part model:
```python
is_deleted = models.BooleanField(default=False, help_text="Mark as deleted if not found in latest sync")
```

## Error Handling

The command includes comprehensive error handling for:
- Excel file not found
- Excel application crashes
- Network timeouts during refresh
- CSV parsing errors
- Database transaction failures
- Missing required columns

## Logging

Enable verbose logging by using the `--verbose` flag or configuring logging in your Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'excel_sync.log',
        },
    },
    'loggers': {
        'dynamics_search.management.commands.sync_from_excel': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Performance Considerations

- **Batch Operations**: Uses bulk_create and bulk_update for efficient database operations
- **Memory Management**: Processes data in batches to avoid memory issues
- **Excel Optimization**: Runs Excel in background mode to reduce resource usage
- **Hash Comparison**: Uses MD5 hashing for fast change detection

## Troubleshooting

### Common Issues

1. **pywin32 Import Error**: Ensure pywin32 is installed on Windows
2. **Excel File Locked**: Close Excel before running the command
3. **Permission Errors**: Ensure the user has read/write access to Excel and CSV files
4. **Network Timeouts**: Increase the `--wait-time` parameter for slow D365 connections

### Debug Mode

Run with verbose output to see detailed progress:
```bash
python manage.py sync_from_excel --verbose --dry-run
```

## Security Considerations

- Excel files should be stored in a secure location
- Consider using environment variables for file paths
- Ensure proper file permissions for the Django user
- Monitor log files for any sync failures

## Monitoring

Set up monitoring for:
- Sync task completion
- Error rates
- Data quality issues
- Performance metrics

Consider using Django admin or a monitoring tool to track sync status and errors.
