"""
create_admin.py
---------------
أمر إدارة (management command) ينشئ حساب مدير (superuser) تلقائياً
وبأمان تام أثناء عملية النشر، بدون أي تفاعل بشري (لا Prompt لكتابة
اسم مستخدم/كلمة مرور، خلافاً لأمر Django الجاهز `createsuperuser`
الذي يتوقف منتظراً إدخالاً يدوياً ويُفشل عملية "Build" غير التفاعلية).

لماذا هذا الأمر "آمن" تحديداً ولا يتعارض مع عملية الـ Build:
1. **Idempotent (نتيجته واحدة دائماً)**: إذا كان المستخدم موجوداً مسبقاً،
   لا يفعل شيئاً ولا يرمي أي خطأ — يمكن تشغيله في كل عملية بناء (Build)
   بأمان تام دون خطر إنشاء حسابات مكررة أو فشل النشر.
2. **غير تفاعلي بالكامل**: يقرأ كل البيانات من متغيرات البيئة، فلا يتوقف
   منتظراً أي إدخال يدوي مطلقاً.
3. **آمن بالتصميم**: لا يحتوي أي كلمة مرور مكتوبة مباشرة في الكود؛ كل
   شيء يُقرأ من متغيرات بيئة تُضبط من لوحة تحكم Render نفسها (لا تظهر
   أبداً في الكود المرفوع على GitHub).

الاستخدام:
    python manage.py create_admin

متغيرات البيئة المطلوبة (اضبطها من Render ← Environment):
    DJANGO_SUPERUSER_USERNAME   (افتراضي: admin)
    DJANGO_SUPERUSER_EMAIL      (افتراضي: admin@example.com)
    DJANGO_SUPERUSER_PASSWORD   (إلزامي فعلياً — بدونه لن يُنشأ أي حساب)
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'ينشئ حساب مدير (superuser) تلقائياً من متغيرات البيئة، بأمان وبدون تكرار.'

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not password:
            # لا نُنشئ حساباً بكلمة مرور فارغة أو متوقَّعة أبداً؛ نتوقف
            # بأمان مع رسالة واضحة بدل المخاطرة بحساب غير آمن.
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_PASSWORD غير مُعرَّف — تم تخطي إنشاء '
                'حساب المدير. أضف هذا المتغير من إعدادات Render إن أردت '
                'إنشاءه تلقائياً.'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f'المستخدم "{username}" موجود بالفعل — لم يُنشأ شيء جديد.'
            ))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f'تم إنشاء حساب المدير "{username}" بنجاح.'
        ))
