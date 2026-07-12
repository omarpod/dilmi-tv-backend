from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'إدارة Dilmi TV'

    def ready(self):
        """
        تخصيصان بسيطان ومستقران للوحة تحكم Django 5 الافتراضية، بدون أي
        مكتبة طرف ثالث (بعد التخلص نهائياً من django-jazzmin الذي سبَّب
        عطل AttributeError: 'super' object has no attribute 'dicts' —
        عطل توافق معروف بين Jazzmin وDjango 5 في قوالب change_form):

        1) عنوان اللوحة (site_header/site_title) من settings.py مباشرة
           — هذه خاصية رسمية موثَّقة من AdminSite نفسه، لا تحتاج أي
           قالب مخصص أو مكتبة إضافية.
        2) حقن إحصائيات بسيطة في صفحة /admin/ الرئيسية فقط (وليس في
           صفحات Add/Change التي سبَّبت العطل سابقاً)، عبر "تغليف"
           الدالة الأصلية index() بدل كتابة AdminSite كامل من الصفر.
        """
        from django.contrib import admin
        from core.dashboard import build_dashboard_stats

        admin.site.site_header = settings.ADMIN_SITE_HEADER
        admin.site.site_title = settings.ADMIN_SITE_TITLE
        admin.site.index_title = settings.ADMIN_INDEX_TITLE

        # اسم مختلف عمداً عن 'admin/index.html' الافتراضي — لو حمل هذا
        # القالب نفس الاسم، فإن {% extends "admin/index.html" %} بداخله
        # كان سيجد نفسه (بما أن مشروعنا مُدرج أولاً في مسارات البحث)،
        # مسبباً "مداً ذاتياً" يُكرر {% block content %} ويفشل التصريف
        # (عطل TemplateSyntaxError واجهناه سابقاً وحُلَّ بهذه التسمية).
        admin.site.index_template = 'admin/dilmi_dashboard.html'

        original_index = admin.site.index

        def index_with_stats(request, extra_context=None):
            extra_context = extra_context or {}
            try:
                extra_context['dilmi_stats'] = build_dashboard_stats()
            except Exception:
                # خط دفاع أخير: حتى لو فشل شيء غير متوقع تماماً (مثل
                # جدول لم تُطبَّق ترحيلاته بعد)، لا تسقط صفحة /admin/
                # بأكملها؛ فقط اعرض القيم الافتراضية الآمنة (صفر).
                extra_context['dilmi_stats'] = {
                    'total_visits': 0, 'visits_last_30_days': 0,
                    'active_subscribers': 0, 'total_channels': 0,
                    'total_news': 0, 'live_matches': 0,
                }
            return original_index(request, extra_context)

        admin.site.index = index_with_stats
