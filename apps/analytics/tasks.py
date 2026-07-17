"""
apps/analytics/tasks.py
--------------------------
يُعيد استخدام أمرَي snapshot_viewers وprune_analytics الموجودين والمُختبَرين
مسبقاً عبر call_command (لا تكرار للكود) — الآن مُجدولان عبر Celery Beat
بدل الاعتماد على Railway Cron Job (راجع CELERY_BEAT_SCHEDULE في
config/settings.py)، بنفس أسلوب apps.streaming.tasks.run_sync_data.
"""
from celery import shared_task
from django.core.management import call_command


@shared_task
def snapshot_viewers():
    call_command('snapshot_viewers')


@shared_task
def prune_analytics():
    call_command('prune_analytics')
