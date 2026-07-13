"""
match_sync.py
--------------
يحوّل بيانات "Free API Live Football Data" لسجلات محلية (League, Team,
Match). مكتوب بأسلوب **دفاعي بالكامل** لأننا لا نملك بعد عيّنة استجابة
حقيقية مؤكدة من هذا المزود الجديد — هذا تحديداً كان سبب الخطأين اللذين
واجهتهما (AttributeError و ImportError) في المحاولة السابقة.

== ⚠️ حالة هذا الملف: مؤقت وآمن، بانتظار عيّنة JSON حقيقية منك ==
كل دالة استخراج (extract_*) أدناه تُجرّب عدة أسماء حقول شائعة، وإن لم
تجد أياً منها، **تُسجّل تحذيراً واضحاً وتتخطى العنصر بأمان** بدل رمي
استثناء يُسقط المزامنة بأكملها. بمجرد أن ترسل لي عيّنة حقيقية من
/football-current-live و/football-fixtures، سأستبدل هذه الدوال بمطابقة
دقيقة 100% للحقول الفعلية.

== لماذا الدوال الثلاث موجودة بالضبط بهذه الأسماء؟ ==
sync_matches.py (أمر الإدارة) يستورد:
    from core.services.match_sync import sync_today_fixtures, sync_live_fixtures_with_events
وsync_fixture مُستخدمة داخلياً بينهما. الإبقاء على نفس الأسماء والتوقيعات
بالضبط يمنع ImportError نهائياً، بغض النظر عن أي تعديل داخلي لاحق.
"""
import logging
from datetime import datetime

from django.utils import timezone

from core.models import League, Team, Match
from core.services.api_football_client import ApiFootballClient, ApiFootballError

logger = logging.getLogger(__name__)


def _first_present(data, *keys, default=None):
    """
    يُرجع أول قيمة موجودة فعلياً وغير فارغة من بين عدة أسماء حقول محتملة
    لنفس المعنى (مثال: 'homeTeam' أو 'home_team' أو 'home'). هذا يحمينا
    من AttributeError/KeyError إذا كان اسم الحقل الحقيقي مختلفاً، **وأيضاً**
    من إنشاء سجلات بقيمة نصية فارغة '' (وليس None فقط) — وهو ما كان يسمح
    بمرور اسم فارغ فعلياً ويُنتج سجلات League/Team معطوبة في قاعدة البيانات.
    """
    if not isinstance(data, dict):
        return default
    for key in keys:
        value = data.get(key)
        if value is not None and value != '':
            return value
    return default


def _extract_list(raw_response):
    """
    استجابات APIs الرياضية عادة تُغلّف القائمة الفعلية داخل مفتاح مثل
    "response" أو "data" أو "matches" أو "result". نُجرّب الاحتمالات
    الشائعة، وإن فشلت كلها ووجدنا قائمة (list) مباشرة كجذر الاستجابة
    نفسها، نستخدمها كما هي.
    """
    if isinstance(raw_response, list):
        return raw_response

    if isinstance(raw_response, dict):
        for key in ('response', 'data', 'matches', 'result', 'results', 'fixtures'):
            value = raw_response.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = _extract_list(value)
                if nested:
                    return nested

    logger.warning(
        'match_sync: تعذّر إيجاد قائمة مباريات داخل الاستجابة. شكل الاستجابة: %s',
        str(raw_response)[:500],
    )
    return []


def _get_or_create_league(fixture_item):
    league_data = _first_present(fixture_item, 'league', 'competition', 'tournament', default={})
    if isinstance(league_data, str):
        # بعض الـ APIs تُرجع اسم البطولة كنص مباشر بدل كائن متداخل —
        # هذا بالضبط نمط الخطأ 'str' object has no attribute 'get' الذي
        # واجهته، ونتعامل معه هنا بأمان بدل الانهيار.
        name = league_data
        external_id = name
    else:
        name = _first_present(league_data, 'name', 'title', default='بطولة غير معروفة')
        external_id = str(_first_present(league_data, 'id', 'leagueId', default=name))

    league, _created = League.objects.get_or_create(
        external_id=external_id,
        defaults={'name': name},
    )
    return league


def _get_or_create_team(team_data):
    if isinstance(team_data, str):
        name = team_data
        external_id = name
    else:
        name = _first_present(team_data, 'name', 'teamName', 'title', default='فريق غير معروف')
        external_id = str(_first_present(team_data, 'id', 'teamId', default=name))

    team, _created = Team.objects.get_or_create(
        external_id=external_id,
        defaults={'name': name},
    )
    return team


def _parse_status(fixture_item):
    status_raw = _first_present(fixture_item, 'status', 'matchStatus', 'state', default='')
    if isinstance(status_raw, dict):
        status_raw = _first_present(status_raw, 'short', 'name', 'type', default='')
    status_raw = str(status_raw).lower()

    if any(word in status_raw for word in ['live', '1h', '2h', 'ht', 'inprogress', 'in_progress']):
        return 'live'
    if any(word in status_raw for word in ['finished', 'ft', 'ended', 'full']):
        return 'finished'
    return 'upcoming'


def sync_fixture(fixture_item):
    """يُزامن مباراة واحدة. يُرجع كائن Match، أو None إذا كانت البيانات ناقصة."""
    if not isinstance(fixture_item, dict):
        logger.warning('match_sync: عنصر مباراة غير متوقع (ليس كائناً): %s', str(fixture_item)[:200])
        return None

    external_id = str(_first_present(fixture_item, 'id', 'matchId', 'fixtureId', default=''))
    if not external_id:
        return None

    home_raw = _first_present(fixture_item, 'homeTeam', 'home_team', 'home', default={})
    away_raw = _first_present(fixture_item, 'awayTeam', 'away_team', 'away', default={})
    if not home_raw or not away_raw:
        logger.warning('match_sync: مباراة %s بدون بيانات فريقين واضحة، تم تخطّيها.', external_id)
        return None

    league = _get_or_create_league(fixture_item)
    home_team = _get_or_create_team(home_raw)
    away_team = _get_or_create_team(away_raw)

    home_score = _first_present(fixture_item, 'homeScore', 'home_score', 'homeGoals', default=0) or 0
    away_score = _first_present(fixture_item, 'awayScore', 'away_score', 'awayGoals', default=0) or 0
    elapsed = _first_present(fixture_item, 'elapsed', 'minute', 'time', default=0)
    if not isinstance(elapsed, (int, float)):
        elapsed = 0

    match_datetime = timezone.now()
    raw_date = _first_present(fixture_item, 'date', 'matchDate', 'kickoff', 'startTime')
    if raw_date:
        try:
            if isinstance(raw_date, (int, float)):
                match_datetime = datetime.fromtimestamp(raw_date, tz=timezone.get_current_timezone())
            else:
                match_datetime = datetime.fromisoformat(str(raw_date).replace('Z', '+00:00'))
        except (ValueError, TypeError):
            logger.warning('match_sync: تعذّر تحليل تاريخ المباراة %s: %s', external_id, raw_date)

    match, _created = Match.objects.update_or_create(
        external_id=external_id,
        defaults={
            'league': league,
            'home_team': home_team,
            'away_team': away_team,
            'match_datetime': match_datetime,
            'status': _parse_status(fixture_item),
            'home_score': int(home_score) if str(home_score).isdigit() else 0,
            'away_score': int(away_score) if str(away_score).isdigit() else 0,
            'elapsed_minutes': int(elapsed) if isinstance(elapsed, (int, float)) else 0,
        },
    )
    return match


def sync_today_fixtures():
    """نقطة الدخول: يجلب مباريات اليوم عبر /football-fixtures ويُزامنها."""
    client = ApiFootballClient()
    today_str = timezone.now().strftime('%Y-%m-%d')

    raw_response = client.get_fixtures_by_date(today_str)
    fixtures = _extract_list(raw_response)

    synced_matches = []
    for fixture_item in fixtures:
        match = sync_fixture(fixture_item)
        if match:
            synced_matches.append(match)

    return synced_matches


def sync_live_fixtures_with_events():
    """
    نقطة الدخول: يجلب المباريات المباشرة الآن عبر /football-current-live.

    ملاحظة: هذا المزود الجديد لم يُؤكَّد بعد أنه يوفر نقطة نهاية منفصلة
    للأحداث (أهداف/بطاقات). هذه الدالة تُزامن المباريات المباشرة فقط
    (بدون أحداث تفصيلية) إلى أن نؤكد ذلك من عيّنة الاستجابة الحقيقية.
    """
    client = ApiFootballClient()

    try:
        raw_response = client.get_live_matches()
    except ApiFootballError as e:
        logger.warning('فشلت مزامنة المباريات المباشرة: %s', e)
        return []

    fixtures = _extract_list(raw_response)

    results = []
    for fixture_item in fixtures:
        match = sync_fixture(fixture_item)
        if match:
            results.append({'match': match, 'new_events': 0})

    return results
