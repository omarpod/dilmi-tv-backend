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


def _apply_admin_theme(sender, **kwargs):
    from django.conf import settings
    from admin_interface.models import Theme

    colors = getattr(settings, 'DILMI_THEME_COLORS', None)
    if not colors:
        return

    theme, _created = Theme.objects.get_or_create(name='Dilmi TV', defaults=colors)
    if not _created:
        # نُحدّث الألوان في كل مرة (وليس فقط عند الإنشاء الأول) حتى تنعكس
        # أي تعديلات مستقبلية على DILMI_THEME_COLORS دون تدخل يدوي بالضغط
        for field, value in colors.items():
            setattr(theme, field, value)
        theme.save()

    # نُفعّلها كثيم نشِط فعلياً (وليس فقط موجودة في القائمة)
    Theme.objects.update(active=False)
    theme.active = True
    theme.save()
