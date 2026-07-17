"""
snapshot_viewers.py
---------------------
يُسجّل لقطة دورية لعدد المشاهدين المباشرين — مصدر خط الاتجاه (Sparkline)
في اللوحة. مُجدوَل الآن عبر Celery Beat كل 5 دقائق (راجع
apps/analytics/tasks.py وCELERY_BEAT_SCHEDULE في config/settings.py) —
هذا الأمر نفسه يبقى قابلاً للتشغيل يدوياً من الطرفية وقت الحاجة.

"مباشر الآن" يُعرَّف هنا بـ: أي جلسة مشاهدة نبضت خلال آخر 90 ثانية (أي
نبضتين تقريباً بمعدل استدعاء كل 30 ثانية من العميل) — هامش يتحمّل فقدان
نبضة واحدة بسبب تذبذب الشبكة دون اعتبار المشاهد "غادر" خطأً.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import ViewerSession, ViewerSnapshot


class Command(BaseCommand):
    help = 'يسجل لقطة لعدد المشاهدين المباشرين حالياً (Sparkline). مُجدوَل عبر Celery Beat.'

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(seconds=90)
        live_viewers = ViewerSession.objects.filter(last_seen__gte=threshold).count()
        ViewerSnapshot.objects.create(live_viewers=live_viewers)
        self.stdout.write(self.style.SUCCESS(f'تم تسجيل لقطة: {live_viewers} مشاهد مباشر.'))
