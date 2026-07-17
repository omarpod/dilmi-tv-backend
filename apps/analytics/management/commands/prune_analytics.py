"""
prune_analytics.py
---------------------
ينظّف بيانات التحليلات القديمة حتى لا يكبر الجدولان بلا حدود:
- ViewerSession: يُحذف السطر إن لم ينبض جهازه منذ أكثر من ساعة (يعني
  المشاهد غادر فعلياً — إبقاؤه كان سيُحصى خطأً ضمن "الأجهزة الفريدة اليوم").
- ViewerSnapshot: نُبقي فقط آخر 30 يوماً (كافية لأي تحليل اتجاه قريب).

مُجدوَل الآن عبر Celery Beat كل ساعة (راجع apps/analytics/tasks.py
وCELERY_BEAT_SCHEDULE في config/settings.py) — هذا الأمر نفسه يبقى
قابلاً للتشغيل يدوياً من الطرفية وقت الحاجة.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import ViewerSession, ViewerSnapshot


class Command(BaseCommand):
    help = 'ينظف جلسات المشاهدة المنتهية ولقطات المشاهدين القديمة. مُجدوَل عبر Celery Beat.'

    def handle(self, *args, **options):
        stale_sessions, _ = ViewerSession.objects.filter(
            last_seen__lt=timezone.now() - timedelta(hours=1),
        ).delete()

        old_snapshots, _ = ViewerSnapshot.objects.filter(
            taken_at__lt=timezone.now() - timedelta(days=30),
        ).delete()

        self.stdout.write(self.style.SUCCESS(
            f'تم حذف {stale_sessions} جلسة منتهية و{old_snapshots} لقطة قديمة.'
        ))
