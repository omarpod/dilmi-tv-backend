"""
apps/core/integrations/push_notifications.py
-------------------------------------------------
إرسال إشعارات Push حقيقية عبر Firebase Cloud Messaging — لموضوعات
(Topics) وليس أجهزة فردية، بما يطابق تصميم تطبيق العميل (يشترك تلقائياً
في match_live وapp_updates دون تسجيل رمز جهاز في قاعدة بياناتنا).

يتطلب متغير بيئة FIREBASE_SERVICE_ACCOUNT_JSON — محتوى ملف Service
Account JSON كاملاً كسطر واحد (وليس مسار ملف)، لأن Railway لا يوفّر
تخزيناً دائماً للملفات. يُنشأ هذا الملف من: Firebase Console → إعدادات
المشروع → Service Accounts → Generate new private key.

بدون هذا المتغير، send_topic_notification لا تفعل شيئاً بصمت (نفس نمط
Cloudinary/RapidAPI في هذا المشروع) — حتى لا يفشل sync_data بالكامل قبل
إعداد Firebase من طرف الفريق.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

_app = None
_init_attempted = False


def _get_app():
    global _app, _init_attempted
    if _init_attempted:
        return _app

    _init_attempted = True
    raw_credentials = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
    if not raw_credentials:
        return None

    import firebase_admin
    from firebase_admin import credentials

    try:
        cert = credentials.Certificate(json.loads(raw_credentials))
        _app = firebase_admin.initialize_app(cert)
    except Exception as e:
        logger.error('فشلت تهيئة Firebase Admin: %s', e, exc_info=True)
        _app = None

    return _app


def send_topic_notification(topic, title, body, data=None):
    """يرجع True إن أُرسل الإشعار فعلياً، False إن كان Firebase غير مُعدّاً
    أو فشل الإرسال (لا يرفع استثناءً — فشل إشعار واحد لا يجب أن يُسقط
    sync_data كاملاً)."""
    app = _get_app()
    if app is None:
        return False

    from firebase_admin import messaging

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        topic=topic,
        data={k: str(v) for k, v in (data or {}).items()},
    )

    try:
        messaging.send(message, app=app)
        return True
    except Exception as e:
        logger.error('فشل إرسال إشعار Push لموضوع %s: %s', topic, e, exc_info=True)
        return False
