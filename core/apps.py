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

        # نخبر Django أن يستخدم قالبنا المُسمّى باسم مختلف عمداً بدل
        # 'admin/index.html' الافتراضي — راجع التعليق التفصيلي أعلى
        # templates/admin/dilmi_dashboard.html لسبب تسميته هكذا تحديداً
        # (تفادي مشكلة "التمديد الذاتي" self-extends).
       # admin.site.index_template = 'admin/dilmi_dashboard.html'

        original_index = admin.site.index

        def index_with_stats(request, extra_context=None):
            extra_context = extra_context or {}
            try:
                extra_context['dilmi_stats'] = build_dashboard_stats()
            except Exception:
                # خط دفاع أخير: حتى لو فشل شيء غير متوقع تماماً داخل
                # build_dashboard_stats نفسها (وليس فقط داخل استعلام واحد
                # كما تحمي _safe_count بالفعل)، لا تسقط صفحة /admin/
                # بأكملها؛ فقط اعرض القيم الافتراضية الآمنة (كلها صفر).
                extra_context['dilmi_stats'] = {
                    'total_visits': 0, 'visits_last_30_days': 0,
                    'active_subscribers': 0, 'total_channels': 0,
                    'total_news': 0, 'live_matches': 0,
                }
            return original_index(request, extra_context)

        admin.site.index = index_with_stats
