import os
import requests

BASE_URL = 'https://free-api-live-football-data.p.rapidapi.com'
API_HOST = 'free-api-live-football-data.p.rapidapi.com'

_FALLBACK_API_KEY = 'fddd70b364msh20579541dd0003bp1e2760jsnfb64dfca3a40'

class ApiFootballError(Exception):
    pass

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
            raise ApiFootballError(f'فشل الاتصال بالـ API: {e}')

        if response.status_code != 200:
            raise ApiFootballError(
                f'الـ API أعاد رمز حالة {response.status_code}: {response.text[:300]}'
            )

        try:
            return response.json()
        except ValueError as e:
            raise ApiFootballError(f'الاستجابة ليست JSON صالحاً: {response.text[:300]}')

    def get_live_matches(self):
        # تم تغيير المسار ليتوافق مع تحديثات الـ API
        return self._get('football-current-live')

    def get_fixtures_by_date(self, date_str=None):
        """
        تم تحديث المسار إلى 'football-fixtures' كمسار أساسي، 
        إذا استمر الـ 404، سنقوم بتغييره إلى 'football-matches'
        """
        params = {'date': date_str} if date_str else {}
        return self._get('football-fixtures', params)
