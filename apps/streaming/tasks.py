"""
apps/streaming/tasks.py
-------------------------
ثلاث مهام يُشغّلها Celery Beat دورياً (راجع CELERY_BEAT_SCHEDULE في
config/settings.py):

1. run_sync_live_matches: المباريات المباشرة الآن فقط (--live-only)،
   كل 5 دقائق حالياً — راجع config/settings.py لضبط الفاصل حسب حصة خطتك.

2. run_sync_data: المزامنة الكاملة (جدول اليوم + الأخبار + تنظيف) كل 30
   دقيقة — يُعيد استخدام أمر sync_data الموجود والمُختبَر مسبقاً (لا
   تكرار للكود). بديل نهائي لحلقة run_sync_loop اليدوية.

3. check_stream_sources_health: فحص خفيف (HEAD) لروابط بث *أضفتموها أنتم*
   في لوحة التحكم — للتأكد أنها لا تزال تستجيب. هذا فحص توفّر لروابط
   تملكونها/رخّصتموها بالفعل، وليس زحفاً على مواقع طرف ثالث، فلا داعي
   لأي Proxy أو تمويه بصمة متصفح هنا.

   مُقيَّد بالقنوات التي "يستحق" فحصها الآن فقط — إما قناة بث دائم عامة
   (بدون ربط بأي مباراة إطلاقاً، كقنوات تبويب "البث المباشر")، أو قناة
   مرتبطة بمباراة مباشرة *الآن* فعلاً. القنوات المرتبطة فقط بمباريات
   قادمة/منتهية تُستبعَد مؤقتاً لتوفير موارد السيرفر (لا فائدة من فحص
   رابط مباراة لم تبدأ بعد أو انتهت)، وتُفحص تلقائياً فور تحوّل مباراتها
   لمباشرة — دون أي إعداد يدوي إضافي.
"""
import logging

import requests
from celery import shared_task
from django.core.management import call_command
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.core.models import Channel, Match

from .models import FAILURE_THRESHOLD, StreamSource

logger = logging.getLogger(__name__)

HEALTH_CHECK_TIMEOUT = 8


@shared_task
def run_sync_live_matches():
    call_command('sync_data', live_only=True)


@shared_task
def run_sync_data():
    call_command('sync_data')


def _channels_worth_checking():
    """قنوات عامة (بدون أي مباراة مرتبطة) أو مرتبطة بمباراة مباشرة الآن."""
    has_live_match = Exists(Match.objects.filter(channel_id=OuterRef('pk'), status=Match.Status.LIVE))
    has_any_match = Exists(Match.objects.filter(channel_id=OuterRef('pk')))
    return Channel.objects.annotate(
        has_live_match=has_live_match, has_any_match=has_any_match,
    ).filter(Q(has_any_match=False) | Q(has_live_match=True)).values('pk')


@shared_task
def check_stream_sources_health():
    sources = StreamSource.objects.filter(
        is_active=True, channel_id__in=_channels_worth_checking(),
    )
    checked = 0
    deactivated = 0

    for source in sources:
        healthy = _probe_url(source.url)
        source.last_checked_at = timezone.now()

        if healthy:
            source.consecutive_failures = 0
            source.is_healthy = True
        else:
            source.consecutive_failures += 1
            source.is_healthy = False
            if source.consecutive_failures >= FAILURE_THRESHOLD:
                source.is_active = False
                deactivated += 1
                logger.warning(
                    'تعطيل رابط البث تلقائياً بعد %s محاولات فاشلة متتالية: %s',
                    FAILURE_THRESHOLD, source.url,
                )

        source.save(update_fields=['is_healthy', 'consecutive_failures', 'last_checked_at', 'is_active'])
        checked += 1

    if deactivated:
        logger.info('فحص روابط البث: %s رابط فُحص، %s عُطِّل تلقائياً.', checked, deactivated)

    return {'checked': checked, 'deactivated': deactivated}


def _probe_url(url, timeout=HEALTH_CHECK_TIMEOUT):
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 405:
            # بعض خوادم HLS لا تدعم HEAD إطلاقاً — نجرّب GET جزئي بدل
            # اعتبار 405 فشلاً فورياً لرابط قد يكون سليماً تماماً
            response = requests.get(url, timeout=timeout, stream=True)
            response.close()
        return response.status_code < 400
    except requests.RequestException:
        return False
