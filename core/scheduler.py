"""
scheduler.py
-------------
مجدوِل خلفي (Background Scheduler) يعمل **داخل نفس عملية Django/Gunicorn**
مباشرة — بديل عملي وخفيف عن Celery+Redis (يتطلبان Background Worker
منفصل مدفوع على Render). يُشغّل sync_news_from_rss() تلقائياً كل 6
ساعات دون أي تدخل يدوي.

== ⚠️ لماذا لا يبدأ هذا تلقائياً في كل مرة (حماية إلزامية) ==
core/apps.py's ready() يُنفَّذ عند **كل** استدعاء لـ manage.py — بما
فيها migrate، createsuperuser، shell، أي أمر آخر — وليس فقط عند تشغيل
السيرفر الفعلي. بدون حماية، سيحاول حتى أمر "makemigrations" البسيط
تشغيل هذا المجدوِل عبثاً. لذلك start_scheduler() هنا **لا تعمل** إلا
إذا كان متغير البيئة ENABLE_SCHEDULER='True' مضبوطاً صراحة — اضبطه
فقط في بيئة تشغيل السيرفر الحقيقي (Start Command على Render)، وليس
في Build Command.

== حدود هذا الحل (بصراحة كاملة) ==
هذا مجدوِل "داخل العملية" (in-process) — إذا أعاد Render تشغيل الخادم
(نشر جديد، أو "نوم" الخطة المجانية)، يتوقف المجدوِل ويبدأ من جديد عند
الإقلاع التالي. مقبول تماماً لسحب أخبار غير حرج التوقيت، لذلك استخدمناه
للأخبار فقط، وليس لمزامنة المباريات المباشرة (تبقى يدوية/عند الطلب).
"""
import logging
import os

logger = logging.getLogger(__name__)

_scheduler_instance = None


def start_scheduler():
    """
    يبدأ المجدوِل الخلفي إن كان مفعَّلاً صراحة عبر ENABLE_SCHEDULER=True،
    وإن لم يكن بدأ مسبقاً في نفس العملية.
    """
    global _scheduler_instance

    if os.environ.get('ENABLE_SCHEDULER') != 'True':
        return  # الوضع الافتراضي الآمن (migrate، shell، إلخ)

    if _scheduler_instance is not None:
        return  # يعمل بالفعل، لا داعي لبدء نسخة ثانية

    from apscheduler.schedulers.background import BackgroundScheduler
    from core.services.rss_news_sync import sync_news_from_rss

    def _scheduled_news_sync():
        try:
            new_articles = sync_news_from_rss()
            logger.info('[المجدوِل الدوري] تمت إضافة %d خبر جديد.', len(new_articles))
        except Exception as e:
            logger.error('[المجدوِل الدوري] فشلت مزامنة الأخبار: %s', e, exc_info=True)

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        _scheduled_news_sync,
        trigger='interval',
        hours=6,
        id='sync_news_periodic',
        replace_existing=True,
    )
    scheduler.start()

    _scheduler_instance = scheduler
    logger.info('تم تشغيل المجدوِل الخلفي بنجاح — سحب الأخبار كل 6 ساعات.')
