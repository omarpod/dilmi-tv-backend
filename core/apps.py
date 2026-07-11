from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'إدارة Dilmi TV'

    def ready(self):
        """
        نُحقن إحصائيات لوحة المعلومات (عدد القنوات، الاشتراكات، الزيارات...)
        في صفحة /admin/ الرئيسية عبر "تغليف" الدالة الأصلية index() الخاصة
        بلوحة تحكم Django، بدل كتابة AdminSite مخصص بالكامل — أبسط وأقل
        عرضة لكسر أي سلوك افتراضي آخر في اللوحة.
        """
        from django.contrib import admin
        from core.dashboard import build_dashboard_stats

        original_index = admin.site.index

        def index_with_stats(request, extra_context=None):
            extra_context = extra_context or {}
            extra_context['dilmi_stats'] = build_dashboard_stats()
            return original_index(request, extra_context)

        admin.site.index = index_with_stats
