"""
probe_api_endpoints.py
------------------------
بدل تصفح واجهة RapidAPI يدوياً (عرضة للخطأ ونسيان تفاصيل)، هذا الأمر
يُجرّب فعلياً قائمة من أسماء المسارات المحتملة لنفس الـ API، ويطبع لك
رمز الحالة (Status Code) لكل واحد — 200 يعني "هذا هو المسار الصحيح"،
404 يعني "غير موجود"، أي رمز آخر (مثل 403) يعني مشكلة صلاحيات منفصلة.

الاستخدام:
    python manage.py probe_api_endpoints

هذا اكتشاف تجريبي حقيقي، وليس تخميناً أو قراءة وثائق غامضة.
"""
import os

import requests
from django.core.management.base import BaseCommand

BASE_URL = 'https://free-api-live-football-data.p.rapidapi.com'
API_HOST = 'free-api-live-football-data.p.rapidapi.com'

# قائمة بأكثر أسماء المسارات شيوعاً في APIs الرياضية المشابهة —
# نجرّبها كلها فعلياً بدل التخمين مرة واحدة والفشل
CANDIDATE_ENDPOINTS = [
    'football-current-live',
    'football-fixtures',
    'matches',
    'live-matches',
    'football-matches',
    'fixtures',
    'football-live',
    'matches-by-date',
    'football-matches-by-date',
    'today-matches',
    'live',
    'current-live',
]


class Command(BaseCommand):
    help = 'يجرّب مسارات API محتملة فعلياً ويطبع رمز الحالة لكل واحد لاكتشاف المسار الصحيح تجريبياً.'

    def handle(self, *args, **options):
        api_key = os.environ.get('API_FOOTBALL_KEY') or 'fddd70b364msh20579541dd0003bp1e2760jsnfb64dfca3a40'

        headers = {
            'x-rapidapi-host': API_HOST,
            'x-rapidapi-key': api_key,
        }

        self.stdout.write(f'يفحص {len(CANDIDATE_ENDPOINTS)} مساراً محتملاً على {BASE_URL} ...')
        self.stdout.write('')

        working_endpoints = []

        for endpoint in CANDIDATE_ENDPOINTS:
            url = f'{BASE_URL}/{endpoint}'
            try:
                response = requests.get(url, headers=headers, timeout=10)
                status = response.status_code

                if status == 200:
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ 200 OK  → /{endpoint}  (هذا مسار صحيح فعلياً!)'
                    ))
                    working_endpoints.append(endpoint)
                    # نطبع أول 200 حرف من الاستجابة كعيّنة سريعة للشكل
                    self.stdout.write(f'     عيّنة من الاستجابة: {response.text[:200]}')
                elif status == 404:
                    self.stdout.write(f'❌ 404      → /{endpoint}  (غير موجود)')
                elif status == 403:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  403      → /{endpoint}  (المسار قد يكون صحيحاً، لكن مشكلة صلاحيات/اشتراك)'
                    ))
                else:
                    self.stdout.write(f'❓ {status}      → /{endpoint}')

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f'⚠️  خطأ اتصال → /{endpoint}: {e}'))

        self.stdout.write('')
        if working_endpoints:
            self.stdout.write(self.style.SUCCESS(
                f'=== المسارات الصحيحة المكتشفة: {working_endpoints} ==='
            ))
            self.stdout.write('حدّث api_football_client.py باستخدام هذه المسارات بالضبط.')
        else:
            self.stdout.write(self.style.ERROR(
                '=== لم يُعثر على أي مسار يُرجع 200 من بين القائمة المُجرَّبة ==='
            ))
            self.stdout.write(
                'هذا يعني أن أسماء المسارات الفعلية مختلفة تماماً عن كل ما جرّبناه. '
                'الحل الوحيد المضمون الآن: افتح صفحة الـ API على RapidAPI ← '
                'تبويب Endpoints (وليس الصفحة الرئيسية) ← اضغط على أي Endpoint ← '
                'انسخ الـ "Base URL" الكامل الظاهر في مثال الكود (curl/Python) '
                'مباشرة من هناك، فهو دائماً دقيق 100%.'
            )
