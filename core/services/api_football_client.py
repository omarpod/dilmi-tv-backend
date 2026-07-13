"""
api_football_client.py
------------------------
طبقة "خام" (Raw Client) للاتصال بمزود "Free API Live Football Data" عبر
RapidAPI. مسؤوليتها الوحيدة: إرسال الطلبات واستقبال JSON، بدون أي منطق
تحويل/حفظ في قاعدة البيانات (ذلك في match_sync.py).

== ✅ نتيجة اكتشاف المسارات (عبر probe_api_endpoints) ==
المسار الوحيد المؤكَّد أنه يعمل فعلياً هو **`/football-current-live`**
(رمز حالة 200). كل مسارات `/fixtures` المُجرَّبة (`football-fixtures`،
`fixtures`، `matches-by-date`...) أعادت 404 — أي أن هذا المزود **لا
يوفّر** نقطة نهاية منفصلة لجلب مباريات حسب تاريخ محدَّد. لذلك حذفنا
`get_fixtures_by_date()` نهائياً بدل تركها معطوبة، واعتمدنا كلياً على
`get_live_matches()` كمصدر البيانات الوحيد المتاح حالياً.

== ⚠️ ملاحظة أمنية مهمة حول المفتاح ==
طلبت دمج المفتاح مباشرة في الكود لتجنّب مشاكل متغيرات البيئة. نفّذنا
هذا، لكن بنمط أكثر أماناً: **متغير البيئة API_FOOTBALL_KEY يُقرأ أولاً
دائماً، والمفتاح المكتوب هنا يُستخدم فقط كقيمة احتياطية إن لم يوجد
المتغير**.
"""
import os
import requests

BASE_URL = 'https://free-api-live-football-data.p.rapidapi.com'
API_HOST = 'free-api-live-football-data.p.rapidapi.com'

# القيمة الاحتياطية (Fallback) — تُستخدم فقط إن لم يوجد متغير البيئة
_FALLBACK_API_KEY = 'fddd70b364msh20579541dd0003bp1e2760jsnfb64dfca3a40'


class ApiFootballError(Exception):
    """يُرفع عند أي فشل في الاتصال بالـ API (مفتاح خاطئ، حد الطلبات
    اليومي انتهى، خطأ شبكة، استجابة غير متوقعة...)."""


class ApiFootballClient:
    def __init__(self):
        self.api_key = os.environ.get('API_FOOTBALL_KEY') or _FALLBACK_API_KEY

    def _headers(self):
        return {
            'x-rapidapi-host': API_HOST,
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
            raise ApiFootballError(f'فشل الاتصال بالـ API: {e}') from e

        if response.status_code != 200:
            raise ApiFootballError(
                f'الـ API أعاد رمز حالة {response.status_code}: {response.text[:300]}'
            )

        try:
            data = response.json()
        except ValueError as e:
            raise ApiFootballError(f'الاستجابة ليست JSON صالحاً: {response.text[:300]}') from e

        return data

    def get_live_matches(self):
        """
        يجلب المباريات المباشرة الآن عبر /football-current-live — هذا هو
        **المصدر الوحيد المتاح** من هذا المزود حالياً (مؤكَّد تجريبياً).

        ⚠️ نُرجع استجابة الـ API "كما هي" (raw) دون افتراض شكلها بعد —
        match_sync.py هو من يتعامل مع استخراج قائمة المباريات منها
        بأسلوب دفاعي، ريثما نؤكد شكلها الدقيق من عيّنة حقيقية.
        """
        return self._get('football-current-live')

