from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create or update superuser'

    def handle(self, *args, **kwargs):
        # البحث عن المستخدم أو إنشاؤه
        user, created = User.objects.get_or_create(username='dilmitv')
        
        # تعيين كلمة المرور بغض النظر إذا كان جديداً أو موجوداً
        user.set_password('jamaldilmi123')
        
        # التأكد من صلاحيات المدير
        user.is_superuser = True
        user.is_staff = True
        
        # حفظ التغييرات
        user.save()
        
        if created:
            self.stdout.write('Superuser created successfully with jamaldilmi123')
        else:
            self.stdout.write('Superuser password updated to jamaldilmi123')
