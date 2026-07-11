from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create superuser'

    def handle(self, *args, **kwargs):
        # نتحقق إذا كان المستخدم موجوداً أم لا قبل الإنشاء
        if not User.objects.filter(username='dilmitv').exists():
            User.objects.create_superuser('dilmitv', 'admin@dilmitv.com', '12345678')
            self.stdout.write('Superuser created!')
        else:
            self.stdout.write('Superuser already exists.')