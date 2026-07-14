"""
run_sync_loop.py
-------------------
بديل عن Railway Cron Job تحديداً لأن خطتك الحالية لا توفّره — يُشغَّل هذا
الأمر كخدمة Railway **منفصلة** عن خدمة الويب (وليس داخل نفس عملية
gunicorn)، ويُكرِّر استدعاء sync_data كل 30 دقيقة (قابل للتعديل) داخل
حلقة مستمرة، بفارق جوهري عن حلقة `while True` "الخام":

== لماذا هذا وليس while True عادية ==
1. **عزل الأخطاء لكل دورة على حدة**: خطأ في دورة واحدة (مثلاً RapidAPI
   متوقف مؤقتاً) يُسجَّل ويُطبع، ثم تُكمل الحلقة للدورة التالية بعد
   Sleep — لا تتوقف العملية بالكامل ولا تحتاج Railway لإعادة تشغيلها.
   حلقة while True "خام" بدون try/except حول كل دورة تتوقف كاملة عند
   أول استثناء غير متوقع، ويعتمد استمرار الخدمة عندها على
   restartPolicyMaxRetries فقط (إعادة تشغيل العملية بأكملها من الصفر
   في كل مرة، وليس فقط تجاوز الدورة الفاشلة).
2. **يُعيد استخدام نفس منطق sync_data.py بالضبط** (المُختبَر مسبقاً) عبر
   call_command — صفر تكرار للكود.
3. **عملية واحدة طويلة العمر بدل تشغيل/إيقاف متكرر**: أخف على الموارد من
   محاولة محاكاة Cron عبر عمليات منفصلة تبدأ وتنتهي باستمرار.

== الإعداد على Railway (خدمة Worker منفصلة) ==
1. من لوحة مشروعك: New Service → اختر نفس المستودع (نفس الكود، نفس
   الفرع) — هذه ستكون خدمة ثانية منفصلة عن خدمة الويب الحالية.
2. Settings → Deploy → Custom Start Command:
       python manage.py run_sync_loop
   (اتركه بدون --interval لاستخدام الافتراضي: 1800 ثانية = 30 دقيقة)
3. Settings → Variables: انسخ نفس متغيرات خدمة الويب (DATABASE_URL
   يُشارَك تلقائياً إن كانتا في نفس المشروع، لكن RAPIDAPI_KEY و
   FIREBASE_SERVICE_ACCOUNT_JSON و NEWS_RSS_FEED_URLS يجب نسخها يدوياً
   لهذه الخدمة الجديدة).
4. **مهم**: لا تضع Build/Start Command لتشغيل collectstatic أو migrate
   هنا — هذه خدمة عاملة فقط (Worker)، خدمة الويب هي المسؤولة عن ذلك.
   يكفي buildCommand بسيط: `pip install -r requirements.txt`.
5. Settings → Restart Policy: اجعله "Always" أو "On Failure" — لو
   تعطّلت الخدمة كاملة لسبب نادر (نفاد الذاكرة مثلاً)، يُعيدها Railway
   تلقائياً، وستستأنف الحلقة من جديد فوراً.
"""
import logging
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 1800  # 30 دقيقة


class Command(BaseCommand):
    help = 'يُشغّل sync_data بشكل دوري داخل حلقة مستمرة — بديل لـ Cron على خطط Railway التي لا توفّره.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval', type=int, default=DEFAULT_INTERVAL_SECONDS,
            help=f'الفاصل بين كل دورة بالثواني (افتراضي: {DEFAULT_INTERVAL_SECONDS} = 30 دقيقة).',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(f'بدء حلقة المزامنة المستمرة — دورة كل {interval} ثانية. (Ctrl+C للإيقاف محلياً)')

        cycle = 0
        while True:
            cycle += 1
            self.stdout.write(f'--- الدورة رقم {cycle} ---')
            try:
                call_command('sync_data')
            except Exception as e:
                # هذا هو الفارق الجوهري عن while True خام: خطأ هنا لا
                # يُنهي العملية بأكملها، فقط يُسجَّل وتُكمل الحلقة
                logger.error('فشلت الدورة رقم %s: %s', cycle, e, exc_info=True)
                self.stdout.write(self.style.ERROR(f'فشلت الدورة رقم {cycle}: {e}'))

            time.sleep(interval)
