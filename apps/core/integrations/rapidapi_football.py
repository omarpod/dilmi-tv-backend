"""
apps/core/integrations/rapidapi_football.py
------------------------------------------------
عميل واجهة "Free API Live Football Data" على RapidAPI. مسؤوليته الوحيدة:
جلب القائمة الخام للمباريات المباشرة كما هي — أي تفسير/تحويل لحقول Match
يتم في sync_data.py عمداً، حتى يبقى هذا الملف بسيطاً وقابلاً لإعادة
الاستخدام أو الاستبدال بمزوّد آخر لاحقاً دون لمس منطق قاعدة البيانات.

ملاحظة أمانة مهمة: لم أتمكن من الوصول لتوثيق شكل الاستجابة الدقيق لهذا
الـ Endpoint تحديداً (صفحات توثيق RapidAPI تحجب الجلب الآلي دون تسجيل
دخول). دالة fetch_live_matches تتعامل مع أشيع أشكال الأغلفة الممكنة
(response/data/result/matches)، وsync_data.py يطبع مفاتيح أول سجل خام
في كل تشغيل — استخدمها إن احتجت تصحيح أسماء الحقول لاحقاً.
"""
import requests

RAPIDAPI_HOST = 'free-api-live-football-data.p.rapidapi.com'
LIVE_MATCHES_URL = f'https://{RAPIDAPI_HOST}/football-current-live'


class RapidApiFootballError(Exception):
    pass


def fetch_live_matches(api_key, timeout=15):
    response = requests.get(
        LIVE_MATCHES_URL,
        headers={'x-rapidapi-key': api_key, 'x-rapidapi-host': RAPIDAPI_HOST},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ('response', 'data', 'result', 'matches'):
            value = payload.get(key)
            if isinstance(value, list):
                return value

    raise RapidApiFootballError(
        'شكل استجابة غير متوقع من free-api-live-football-data — '
        f'المفاتيح الموجودة: {list(payload) if isinstance(payload, dict) else type(payload).__name__}'
    )
