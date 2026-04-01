"""
Celery — MonaJent
─────────────────
Configuration de l'application Celery et du planning Beat.

Lancement :
  # Worker
  celery -A config worker -l info

  # Beat (scheduler)
  celery -A config beat -l info

  # Tout-en-un (dev seulement)
  celery -A config worker -B -l info
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('monajent')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# ── Planning Beat ────────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    'expire-listings-every-hour': {
        'task': 'apps.core.tasks.expire_listings_task',
        'schedule': crontab(minute=0),  # Toutes les heures pile
    },
    'auto-cancel-visits-every-30min': {
        'task': 'apps.core.tasks.auto_cancel_visits_task',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
    },
    'cleanup-media-weekly': {
        'task': 'apps.core.tasks.cleanup_media_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Dimanche 3h du matin
    },
}
