import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kemco_portal.settings')

app = Celery('kemco_portal')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-parts-daily': {
        'task': 'dynamics_search.tasks.sync_parts_from_excel_task',
        'schedule': crontab(hour=3, minute=0),  # Every day at 3 AM
        'args': (),
        'options': {'queue': 'default'},
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
