"""
ensure_superuser.py
---------------------
ينشئ حساب مدير (superuser) تلقائياً من متغيرات بيئة Railway عند كل عملية
نشر (Deploy) — بدلاً من الاعتماد على `python manage.py createsuperuser`
التفاعلي، الذي لا يعمل أصلاً داخل Railway (لا يوجد طرفية تفاعلية في
خطوة الـ Start Command، وفتح "Console" من واجهة Railway له بيئة منفصلة
لا تُفعِّل بالضرورة نفس الحزم المثبَّتة، وهو مصدر خطأ
`ModuleNotFoundError: No module named 'django'` الذي واجهته سابقاً).

آمن للتشغيل في كل عملية نشر (idempotent):
- إن لم تكن متغيرات البيئة الثلاثة مضبوطة، لا يفعل شيئاً (صامت).
- إن كان المستخدم موجوداً مسبقاً، يُحدِّث كلمة المرور فقط (لا يفشل
  بخطأ "IntegrityError: username already exists").
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'ينشئ/يُحدِّث حساب superuser من متغيرات البيئة DJANGO_SUPERUSER_*.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(
                'DJANGO_SUPERUSER_USERNAME أو DJANGO_SUPERUSER_PASSWORD غير '
                'مضبوطين — تم تخطي إنشاء حساب المدير.'
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True},
        )

        user.email = email or user.email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = 'تم إنشاء' if created else 'تم تحديث'
        self.stdout.write(self.style.SUCCESS(f'{action} حساب المدير "{username}" بنجاح.'))
