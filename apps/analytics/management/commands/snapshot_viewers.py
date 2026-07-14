"""
snapshot_viewers.py
---------------------
يُسجّل لقطة دورية لعدد المشاهدين المباشرين — مصدر خط الاتجاه (Sparkline)
في اللوحة. مُصمَّم للتشغيل عبر Railway Cron Job كل 5 دقائق مثلاً (بنفس
أسلوب sync_data.py في apps/core — راجع تعليقاته لخطوات إعداد Cron Job
جديد على Railway).

"مباشر الآن" يُعرَّف هنا بـ: أي جلسة مشاهدة نبضت خلال آخر 90 ثانية (أي
نبضتين تقريباً بمعدل استدعاء كل 30 ثانية من العميل) — هامش يتحمّل فقدان
نبضة واحدة بسبب تذبذب الشبكة دون اعتبار المشاهد "غادر" خطأً.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import ViewerSession, ViewerSnapshot


class Command(BaseCommand):
    help = 'يسجل لقطة لعدد المشاهدين المباشرين حالياً (Sparkline). للتشغيل عبر Railway Cron Job.'

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(seconds=90)
        live_viewers = ViewerSession.objects.filter(last_seen__gte=threshold).count()
        ViewerSnapshot.objects.create(live_viewers=live_viewers)
        self.stdout.write(self.style.SUCCESS(f'تم تسجيل لقطة: {live_viewers} مشاهد مباشر.'))
