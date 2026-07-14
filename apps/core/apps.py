from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'إدارة Dilmi TV'

    def ready(self):
        """
        نُطبِّق ألوان DILMI_THEME_COLORS على django-admin-interface تلقائياً
        — لكن **بعد** كل migrate تحديداً (عبر إشارة post_migrate)، وليس
        مباشرة هنا. السبب: جدول Theme الخاص بـ admin_interface نفسه قد
        لا يكون موجوداً بعد أول تشغيل (قبل أول migrate)، فالاستعلام عنه
        هنا مباشرة قد يفشل. post_migrate يضمن أن الجدول موجود دائماً
        قبل محاولة الكتابة إليه.
        """
        from django.db.models.signals import post_migrate
        post_migrate.connect(_apply_admin_theme, sender=self)

        _install_dashboard()


def _apply_admin_theme(sender, **kwargs):
    from django.conf import settings
    from admin_interface.models import Theme

    colors = getattr(settings, 'DILMI_THEME_COLORS', None)
    if not colors:
        return

    theme, _created = Theme.objects.get_or_create(name='Dilmi TV', defaults=colors)
    # نُطبِّق الألوان الافتراضية *مرة واحدة فقط* عند الإنشاء الأول. لو طبّقناها
    # في كل migrate (كما كان سابقاً)، أي تخصيص يدوي لاحق من طرف الفريق —
    # مثل رفع شعار (logo) من واجهة /admin/admin_interface/theme/ — كان
    # سيُمحى تلقائياً عند أول Deploy تالٍ لأن post_migrate يُعيد ضبط القيم
    # من DILMI_THEME_COLORS في كل مرة. الآن: بعد الإنشاء الأول، الثيم مملوك
    # بالكامل لواجهة الإدارة، ولا نلمسه برمجياً مجدداً.

    # نُفعّلها كثيم نشِط فعلياً (وليس فقط موجودة في القائمة) — هذا فقط، دائماً
    if not theme.active:
        Theme.objects.update(active=False)
        theme.active = True
        theme.save(update_fields=['active'])


def _install_dashboard():
    """
    يُلحِق إحصائيات حيّة (عدد المباريات، المباشرة الآن، القنوات، الأخبار)
    بصفحة /admin/ الرئيسية، ليقرأها templates/admin/index.html.

    لماذا Monkey-patch لـ AdminSite.index بدل إنشاء AdminSite مخصَّص:
    admin.site هو الكائن الوحيد (singleton) الذي يستخدمه @admin.register
    في كل الملفات (admin.py) — استبداله بكائن آخر يتطلب إعادة تسجيل كل
    النماذج يدوياً. تعديل الدالة المرتبطة به مباشرة أبسط وأكثر أماناً هنا.
    """
    from django.contrib import admin
    from django.contrib.admin.sites import AdminSite

    original_index = AdminSite.index

    def index_with_dashboard(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['dashboard'] = _dashboard_context()
        return original_index(self, request, extra_context)

    admin.site.index = index_with_dashboard.__get__(admin.site, AdminSite)


def _dashboard_context():
    from .models import Channel, Match, News

    matches = Match.objects.select_related('channel')
    live_matches = matches.filter(status='live').order_by('-elapsed_minutes')[:8]

    return {
        'stats': {
            'total_matches': matches.count(),
            'live_now': matches.filter(status='live').count(),
            'active_channels': Channel.objects.filter(is_active=True).count(),
            'published_news': News.objects.filter(is_published=True).count(),
        },
        'live_matches': live_matches,
    }
