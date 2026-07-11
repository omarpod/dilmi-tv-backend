from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create or update superuser'

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(username='dilmitv')
        if created:
            user.set_password('jamaldilmi123')
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write('Superuser created!')
        else:
            # إذا كان المستخدم موجوداً، سنقوم بتحديث كلمة السر لضمان الدخول
            user.set_password('jamaldilmi123')
            user.save()
            self.stdout.write('Superuser password updated!')
