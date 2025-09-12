from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def sync_excel_data():
    """
    Celery task to sync data from Excel file.
    This task can be scheduled to run daily at 3 AM or hourly.
    """
    try:
        logger.info("Starting scheduled Excel sync task...")
        
        # Call the management command
        call_command(
            'sync_from_excel',
            excel_path='path/to/d365_parts.xlsx',
            csv_path='parts_export.csv',
            wait_time=30,
            verbosity=1
        )
        
        logger.info("Excel sync task completed successfully")
        return "Excel sync completed successfully"
        
    except Exception as e:
        logger.error(f"Excel sync task failed: {str(e)}")
        raise e

@shared_task
def sync_excel_data_hourly():
    """
    Hourly sync task with shorter wait time for more frequent updates.
    """
    try:
        logger.info("Starting hourly Excel sync task...")
        
        # Call the management command with shorter wait time
        call_command(
            'sync_from_excel',
            excel_path='path/to/d365_parts.xlsx',
            csv_path='parts_export_hourly.csv',
            wait_time=15,  # Shorter wait time for hourly sync
            verbosity=1
        )
        
        logger.info("Hourly Excel sync task completed successfully")
        return "Hourly Excel sync completed successfully"
        
    except Exception as e:
        logger.error(f"Hourly Excel sync task failed: {str(e)}")
        raise e
