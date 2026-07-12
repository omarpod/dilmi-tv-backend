"""
sync_matches.py
-----------------
أمر إدارة يدوي لمزامنة المباريات من API-Football. يعمل الآن **بدون أي
حاجة لـ Celery أو Redis** — تُشغّله يدوياً كلما أردت تحديث البيانات:

    python manage.py sync_matches                # كل مباريات اليوم
    python manage.py sync_matches --live-only     # المباريات المباشرة فقط + أحداثها

== الترقية لأتمتة كاملة لاحقاً (المرحلة 2، عند توفر Redis/Celery) ==
بدل تشغيل هذا الأمر يدوياً، ستُنشئ مهمة Celery دورية تستدعي بالضبط نفس
الدوال من core/services/match_sync.py (sync_today_fixtures كل ساعة،
sync_live_fixtures_with_events كل دقيقة) — منطق المزامنة نفسه لن يتغيّر
حرفاً واحداً، فقط "من يستدعيه ومتى" يتغيّر.

== بديل مؤقت للأتمتة الآن (بدون Celery) ==
إذا أردت تحديثاً تلقائياً دورياً الآن دون انتظار الترقية، يمكنك استخدام
خدمة خارجية مجانية مثل cron-job.org لاستدعاء رابط محمي في تطبيقك كل
بضع دقائق (يتطلب إضافة view خاص يُشغّل هذا المنطق عبر HTTP بدل سطر
الأوامر) — أخبرني إن أردت هذا الحل الوسيط، يمكن إضافته بسرعة.
"""
from django.core.management.base import BaseCommand

from core.services.match_sync import (
    sync_today_fixtures, sync_live_fixtures_with_events,
)
from core.services.api_football_client import ApiFootballError


class Command(BaseCommand):
    help = 'يُزامن المباريات من API-Football مع قاعدة البيانات المحلية.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--live-only', action='store_true',
            help='زامن فقط المباريات المباشرة الآن (مع أحداثها)، بدل كل مباريات اليوم.',
        )

    def handle(self, *args, **options):
        try:
            if options['live_only']:
                results = sync_live_fixtures_with_events()
                self.stdout.write(self.style.SUCCESS(
                    f'تمت مزامنة {len(results)} مباراة مباشرة، '
                    f'بإجمالي {sum(r["new_events"] for r in results)} حدث جديد.'
                ))
            else:
                matches = sync_today_fixtures()
                self.stdout.write(self.style.SUCCESS(
                    f'تمت مزامنة {len(matches)} مباراة لهذا اليوم.'
                ))
        except ApiFootballError as e:
            # نطبع رسالة واضحة بدل traceback مخيف — الأسباب الشائعة:
            # مفتاح API غير مُعرَّف، أو تجاوز الحد اليومي المجاني للطلبات
            self.stdout.write(self.style.ERROR(f'فشلت المزامنة: {e}'))
