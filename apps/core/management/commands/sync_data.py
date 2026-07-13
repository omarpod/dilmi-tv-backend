"""
sync_data.py
-------------
أمر سحب البيانات الدوري (مباريات + أخبار) — **مُصمَّم خصيصاً ليعمل عبر
Railway Cron Job**، وليس Celery أو APScheduler.

== لماذا Railway Cron Job هو "الطريقة المثلى" التي طلبتها (وليس APScheduler) ==
1. **بلا كود إضافي للجدولة نفسها**: Railway يُشغّل هذا الأمر تلقائياً
   حسب جدول Cron تضبطه من الواجهة مباشرة — لا حاجة لأي مكتبة جدولة
   (APScheduler/Celery Beat) داخل كودك إطلاقاً.
2. **معزول تماماً عن خدمة الويب**: يعمل كخدمة Railway منفصلة (نفس
   المستودع، Start Command مختلف)، فلا يستهلك موارد Gunicorn أو يخاطر
   بتعطيل الموقع الرئيسي إن فشل.
3. **شرط إلزامي من Railway نفسه**: يجب أن **ينتهي وينهي العملية (exit)
   فور اكتمال المهمة** — Railway لا يُنهي العمليات تلقائياً؛ إن بقيت
   عملية سابقة "عالقة"، يتجاهل Railway أي تشغيل جديد مجدوَل حتى تنتهي
   الأولى. لهذا الأمر هنا يُنفّذ المهمة ثم يخرج مباشرة، دون أي حلقة
   `while True` أو اتصال مفتوح يبقيه حيّاً.

== إعداد Cron Job في Railway (خطوات) ==
1. من لوحة مشروعك على Railway: New Service → اختر نفس المستودع (Repo)
2. في إعدادات الخدمة الجديدة (وليس خدمة الويب الأصلية):
   Settings → Deploy → Custom Start Command:
       python manage.py sync_data
3. في نفس الصفحة: Settings → Cron Schedule، أدخل تعبير Cron، مثال:
       */15 * * * *     (كل 15 دقيقة — للمباريات المباشرة)
4. Railway يُشغّل هذا تلقائياً حسب الجدول — بدون أي كود جدولة إضافي.

ملاحظة: جدولة Railway بتوقيت UTC دائماً — ضع هذا في اعتبارك عند اختيار
تكرار التشغيل.
"""
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'يسحب المباريات والأخبار من مصادر خارجية. مُصمَّم للتشغيل عبر Railway Cron Job.'

    def handle(self, *args, **options):
        self.stdout.write('بدء المزامنة الدورية...')

        try:
            matches_synced = self._sync_matches()
            self.stdout.write(self.style.SUCCESS(f'تمت مزامنة {matches_synced} مباراة.'))
        except Exception as e:
            # لا نرفع الاستثناء للأعلى (sys.exit بكود خطأ) عمداً هنا —
            # فشل مصدر بيانات واحد (مثلاً API المباريات متوقف مؤقتاً)
            # لا يجب أن يمنع تشغيل مزامنة الأخبار في نفس هذا التشغيل
            logger.error('فشلت مزامنة المباريات: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشلت مزامنة المباريات: {e}'))

        try:
            news_synced = self._sync_news()
            self.stdout.write(self.style.SUCCESS(f'تمت إضافة {news_synced} خبر جديد.'))
        except Exception as e:
            logger.error('فشلت مزامنة الأخبار: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشلت مزامنة الأخبار: {e}'))

        self.stdout.write('انتهت المزامنة — العملية ستُغلق الآن (متطلَّب من Railway Cron).')

    def _sync_matches(self):
        """
        اربط هنا استدعاء عميل API المباريات الحقيقي الخاص بك (نفس نمط
        ApiFootballClient الذي بنيناه سابقاً في المشروع القديم — يمكن
        نقله لهذا المشروع الجديد كما هو، الهيكل نفسه لا يزال صالحاً).
        """
        # مثال هيكلي فقط — استبدله بالاستدعاء الفعلي لمصدرك
        return 0

    def _sync_news(self):
        """اربط هنا استدعاء rss_news_sync (نفس الملف من المشروع القديم قابل للنقل مباشرة)."""
        return 0
