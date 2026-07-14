"""
announce_update.py
---------------------
يُرسل إشعار Push يدوياً لكل مستخدمي التطبيق (موضوع app_updates) — يُستخدم
عند نشر إصدار جديد من تطبيق الموبايل على المتاجر. تشغيل يدوي فقط (وليس
Cron)، من نفس بيئة الويب على Railway مباشرة عبر "Run Command" أو من جهازك
محلياً بعد ضبط DATABASE_URL/FIREBASE_SERVICE_ACCOUNT_JSON.

مثال:
    python manage.py announce_update "تحديث جديد متوفر! حمّله الآن لتجربة أفضل."
"""
from django.core.management.base import BaseCommand, CommandError

from apps.core.integrations.push_notifications import send_topic_notification


class Command(BaseCommand):
    help = 'يرسل إشعار Push لكل المستخدمين (موضوع app_updates) — لإعلانات التحديثات.'

    def add_arguments(self, parser):
        parser.add_argument('message', type=str, help='نص الإشعار الذي سيراه المستخدمون')
        parser.add_argument('--title', type=str, default='تحديث جديد', help='عنوان الإشعار')

    def handle(self, *args, **options):
        sent = send_topic_notification(
            topic='app_updates',
            title=options['title'],
            body=options['message'],
        )

        if sent:
            self.stdout.write(self.style.SUCCESS('تم إرسال الإشعار بنجاح.'))
        else:
            raise CommandError(
                'فشل الإرسال — تأكد أن FIREBASE_SERVICE_ACCOUNT_JSON مضبوط بشكل صحيح في متغيرات البيئة.'
            )
