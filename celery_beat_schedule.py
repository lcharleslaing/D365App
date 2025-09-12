"""
Celery Beat schedule configuration for Excel sync tasks.
Run with: celery -A kemco_portal beat --loglevel=info
"""

from celery.schedules import crontab

# Celery Beat schedule configuration
CELERY_BEAT_SCHEDULE = {
    # Daily sync at 3:00 AM
    'daily-excel-sync': {
        'task': 'dynamics_search.tasks.sync_excel_data',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM daily
    },
    
    # Hourly sync (optional - uncomment if needed)
    # 'hourly-excel-sync': {
    #     'task': 'dynamics_search.tasks.sync_excel_data_hourly',
    #     'schedule': crontab(minute=0),  # Every hour at minute 0
    # },
    
    # Alternative: Every 6 hours
    # 'six-hourly-excel-sync': {
    #     'task': 'dynamics_search.tasks.sync_excel_data',
    #     'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours
    # },
}

# Timezone for scheduled tasks
CELERY_TIMEZONE = 'UTC'  # Change to your timezone if needed
