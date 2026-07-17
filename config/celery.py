"""
config/celery.py
-----------------
تطبيق Celery — يُشغَّل كعمليتين منفصلتين عن خدمة الويب (gunicorn):
    celery -A config worker    # يُنفّذ المهام
    celery -A config beat      # يُجدولها دورياً (CELERY_BEAT_SCHEDULE في settings.py)

فصل worker عن beat مقصود: يسمح بتشغيل عدة نسخ من worker للتوسّع الأفقي
(docker compose up --scale worker=3) دون خطر تنفيذ نفس المهمة المجدولة
عدة مرات في نفس اللحظة — وهو خطر حقيقي لو استُخدم `-B` المدمج مع عدة عمّال.
"""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('dilmi_tv')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
