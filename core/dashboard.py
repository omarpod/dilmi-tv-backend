"""
dashboard.py
------------
يحسب الأرقام التي تظهر في بطاقات الإحصائيات أعلى صفحة /admin/ الرئيسية
(مثل "إجمالي المشاهدات" و "المشتركون الجدد" في الصورة المرجعية).

فصلنا هذا المنطق في ملف مستقل (بدل كتابته مباشرة داخل apps.py) حتى يسهل
اختباره أو تعديله لاحقاً دون لمس دورة حياة التطبيق (AppConfig.ready).
"""
from datetime import timedelta
from django.utils import timezone

from .models import Channel, Match, News, Analytics, NotificationSubscriber


def build_dashboard_stats():
    """يُرجع قاموساً بكل الأرقام التي يعرضها قالب admin/index.html المخصص."""
    last_30_days = timezone.now() - timedelta(days=30)

    return {
        # إجمالي المشاهدات (كل الزيارات المسجَّلة منذ بداية التشغيل)
        'total_visits': Analytics.objects.count(),

        # زيارات آخر 30 يوماً فقط (رقم أكثر دلالة من "الإجمالي" وحده)
        'visits_last_30_days': Analytics.objects.filter(timestamp__gte=last_30_days).count(),

        # "المشتركون الجدد": أجهزة سجّلت رمز إشعارات نشِط (تقريب مقبول
        # لمفهوم "مشترك" بما أن المشروع لا يملك نظام تسجيل دخول للمستخدمين)
        'active_subscribers': NotificationSubscriber.objects.filter(is_active=True).count(),

        'total_channels': Channel.objects.filter(is_active=True).count(),
        'total_news': News.objects.filter(is_published=True).count(),

        # مباريات مباشرة الآن تحديداً — رقم "حي" يعطي إحساس لوحة تشغيل حقيقية
        'live_matches': Match.objects.filter(status='live').count(),
    }
