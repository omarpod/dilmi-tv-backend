"""
api_football_client.py
------------------------
طبقة "خام" (Raw Client) للاتصال بمزود "Free API Live Football Data" عبر
RapidAPI. مسؤوليتها الوحيدة: إرسال الطلبات واستقبال JSON، بدون أي منطق
تحويل/حفظ في قاعدة البيانات (ذلك في match_sync.py).

== ⚠️ ملاحظة أمنية مهمة حول المفتاح ==
طلبت دمج المفتاح مباشرة في الكود لتجنّب مشاكل متغيرات البيئة. نفّذنا
هذا، لكن بنمط أكثر أماناً: **متغير البيئة API_FOOTBALL_KEY يُقرأ أولاً
دائماً، والمفتاح المكتوب هنا يُستخدم فقط كقيمة احتياطية إن لم يوجد
المتغير**. النتيجة العملية: الكود يعمل فوراً بدون أي إعداد إضافي (كما
طلبت)، لكن يبقى بإمكانك حماية المفتاح لاحقاً بضبط المتغير على Render
دون تعديل الكود مطلقاً.

بما أن مستودعك مرفوع على GitHub، **ضع في اعتبارك تدوير (تغيير) هذا
المفتاح من لوحة RapidAPI لاحقاً** إذا كان المستودع عاماً (Public) أو قد
يصبح كذلك — أي شخص يصل لهذا الملف يرى المفتاح.
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
        يجلب المباريات المباشرة الآن عبر /football-current-live.

        ⚠️ نُرجع استجابة الـ API "كما هي" (raw) دون افتراض شكلها بعد —
        match_sync.py هو من يتعامل مع استخراج قائمة المباريات منها،
        بمجرد أن نعرف شكلها الحقيقي من العيّنة التي سترسلها.
        """
        return self._get('football-current-live')

    def get_fixtures_by_date(self, date_str=None):
        """
        يجلب المباريات حسب التاريخ عبر /football-fixtures.
        [date_str] بصيغة YYYY-MM-DD؛ إن تُرك فارغاً، نعتمد على السلوك
        الافتراضي لهذا الـ API (على الأرجح يومه الحالي، سنؤكد هذا من
        العيّنة الحقيقية أيضاً).
        """
        params = {'date': date_str} if date_str else {}
        return self._get('football-fixtures', params)
