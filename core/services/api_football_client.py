"""
api_football_client.py
------------------------
طبقة "خام" (Raw Client) للاتصال بـ API-Football عبر RapidAPI. مسؤوليتها
الوحيدة: إرسال الطلبات واستقبال JSON، بدون أي منطق حفظ في قاعدة البيانات
(ذلك في match_sync.py). هذا الفصل يجعل الكود قابلاً للاختبار بسهولة،
وجاهزاً لأن يُستدعى لاحقاً من داخل مهمة Celery دورية دون أي تعديل —
فقط استبدال "من يستدعي هذه الدالة" (أمر يدوي الآن، مهمة Celery لاحقاً).

== كيف تحصل على مفتاح API-Football؟ ==
1. أنشئ حساباً على https://rapidapi.com
2. ابحث عن "API-FOOTBALL" واشترك (توجد خطة مجانية محدودة، ثم خطط مدفوعة)
3. من صفحة الـ API، انسخ "X-RapidAPI-Key" الخاص بك
4. أضفه كمتغير بيئة في Render باسم: API_FOOTBALL_KEY
"""
import os
import requests

BASE_URL = 'https://api-football-v1.p.rapidapi.com/v3'


class ApiFootballError(Exception):
    """يُرفع عند أي فشل في الاتصال بـ API-Football (مفتاح مفقود، حد الطلبات
    اليومي انتهى، خطأ شبكة...)، حتى يُميَّز بوضوح عن أي استثناء آخر."""


class ApiFootballClient:
    def __init__(self):
        self.api_key = os.environ.get('API_FOOTBALL_KEY')

    def _headers(self):
        if not self.api_key:
            raise ApiFootballError(
                'متغير البيئة API_FOOTBALL_KEY غير مُعرَّف. أضفه من إعدادات '
                'Render ← Environment قبل تشغيل المزامنة.'
            )
        return {
            'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
            'x-rapidapi-key': self.api_key,
        }

    def _get(self, endpoint, params=None):
        try:
            response = requests.get(
                f'{BASE_URL}/{endpoint}',
                headers=self._headers(),
                params=params or {},
                timeout=20,
            )
        except requests.RequestException as e:
            raise ApiFootballError(f'فشل الاتصال بـ API-Football: {e}') from e

        if response.status_code != 200:
            raise ApiFootballError(
                f'API-Football أعاد رمز حالة {response.status_code}: {response.text[:300]}'
            )

        data = response.json()
        # API-Football يُرجع أخطاءه الخاصة داخل الاستجابة نفسها (وليس عبر
        # رمز HTTP دائماً)، مثال: تجاوز الحد اليومي للطلبات
        if data.get('errors'):
            raise ApiFootballError(f'API-Football أعاد خطأ: {data["errors"]}')

        return data.get('response', [])

    def get_fixtures_by_date(self, date_str):
        """يجلب كل مباريات يوم معيّن (بصيغة YYYY-MM-DD) عبر كل البطولات."""
        return self._get('fixtures', {'date': date_str})

    def get_live_fixtures(self):
        """يجلب كل المباريات المباشرة الآن في العالم (نداء أخف من جلب كل شيء)."""
        return self._get('fixtures', {'live': 'all'})

    def get_fixture_events(self, fixture_external_id):
        """يجلب أحداث مباراة واحدة (أهداف، بطاقات، تبديلات)."""
        return self._get('fixtures/events', {'fixture': fixture_external_id})
