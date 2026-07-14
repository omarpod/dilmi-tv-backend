"""
prune_analytics.py
---------------------
ينظّف بيانات التحليلات القديمة حتى لا يكبر الجدولان بلا حدود:
- ViewerSession: يُحذف السطر إن لم ينبض جهازه منذ أكثر من ساعة (يعني
  المشاهد غادر فعلياً — إبقاؤه كان سيُحصى خطأً ضمن "الأجهزة الفريدة اليوم").
- ViewerSnapshot: نُبقي فقط آخر 30 يوماً (كافية لأي تحليل اتجاه قريب).

مُصمَّم للتشغيل عبر Railway Cron Job (مرة كل ساعة مثلاً) — بنفس أسلوب
sync_data.py و snapshot_viewers.py.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import ViewerSession, ViewerSnapshot


class Command(BaseCommand):
    help = 'ينظف جلسات المشاهدة المنتهية ولقطات المشاهدين القديمة. للتشغيل عبر Railway Cron Job.'

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
