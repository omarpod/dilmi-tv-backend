"""
dashboard.py
------------
يحسب الأرقام التي تظهر في بطاقات الإحصائيات أعلى صفحة /admin/ الرئيسية.

مبدأ التصميم المهم هنا: **لا يجب أبداً أن يُسقط فشل حساب رقم واحد
(مثلاً بسبب جدول مفقود إن لم تُنفَّذ الترحيلات الأخيرة بعد على خادم
معيّن) صفحة /admin/ بأكملها بخطأ 500**. لذلك كل استعلام محمي بمفرده،
ويُعرض 0 كقيمة احتياطية آمنة بدل رمي استثناء يوقف الصفحة كاملة.
"""
import logging
from datetime import timedelta
from django.utils import timezone

from .models import Channel, Match, News, Analytics, NotificationSubscriber

logger = logging.getLogger(__name__)


def _safe_count(queryset_func, default=0):
    """
    يُنفّذ دالة تُرجع رقماً (عادة .count()) وتُعيد قيمة احتياطية آمنة
    عند أي خطأ (جدول مفقود، عمود مفقود، أو أي مشكلة أخرى غير متوقعة في
    قاعدة البيانات)، بدل إسقاط صفحة /admin/ بأكملها بخطأ 500.
    """
    try:
        return queryset_func()
    except Exception:
        # نُسجّل الخطأ في السجلات (logs) للمطوّر، لكن لا نُظهره للمستخدم
        # ولا نوقف الصفحة — الإحصائيات ميزة إضافية، وليست وظيفة أساسية
        # يستحق فشلها إسقاط لوحة التحكم بأكملها.
        logger.warning('فشل حساب إحصائية في dashboard.py', exc_info=True)
        return default


def build_dashboard_stats():
    """يُرجع قاموساً بكل الأرقام التي يعرضها قالب admin/dilmi_dashboard.html."""
    last_30_days = timezone.now() - timedelta(days=30)

    return {
        'total_visits': _safe_count(lambda: Analytics.objects.count()),
        'visits_last_30_days': _safe_count(
            lambda: Analytics.objects.filter(timestamp__gte=last_30_days).count()
        ),
        'active_subscribers': _safe_count(
            lambda: NotificationSubscriber.objects.filter(is_active=True).count()
        ),
        'total_channels': _safe_count(lambda: Channel.objects.filter(is_active=True).count()),
        'total_news': _safe_count(lambda: News.objects.filter(is_published=True).count()),
        'live_matches': _safe_count(lambda: Match.objects.filter(status='live').count()),
    }
