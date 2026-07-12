"""
match_sync.py
--------------
"الدماغ" الفعلي للأتمتة: يأخذ بيانات خام من ApiFootballClient ويحوّلها
لسجلات محلية (League, Team, Match, MatchEvent) عبر "upsert" آمن بالكامل
(get_or_create / update_or_create)، بحيث تشغيل المزامنة عشرات المرات
لا يُنشئ أي تكرار إطلاقاً — يعتمد كلياً على external_id كمفتاح تطابق.

== لماذا هذا الملف منفصل عن management/commands/sync_matches.py؟ ==
هذا الفصل (Service Layer) يعني أن نفس هذا الكود بالضبط يمكن استدعاؤه
لاحقاً من:
  - أمر يدوي (كما الآن): python manage.py sync_matches
  - مهمة Celery دورية (المرحلة القادمة): @shared_task def sync_task(): ...
  - رابط API محمي يستدعيه المدير بضغطة زر من لوحة التحكم
بدون تعديل حرف واحد من منطق المزامنة نفسه.
"""
import logging
from datetime import datetime

from django.utils import timezone

from core.models import League, Team, Match, MatchEvent
from core.services.api_football_client import ApiFootballClient, ApiFootballError

logger = logging.getLogger(__name__)


# تحويل رموز حالة API-Football المختصرة إلى قيم STATUS_CHOICES عندنا.
# القائمة الكاملة للرموز موثَّقة في: api-football.com/documentation-v3
STATUS_MAP = {
    'TBD': 'upcoming', 'NS': 'upcoming', 'PST': 'upcoming',
    '1H': 'live', 'HT': 'live', '2H': 'live', 'ET': 'live',
    'BT': 'live', 'P': 'live', 'SUSP': 'live', 'INT': 'live',
    'FT': 'finished', 'AET': 'finished', 'PEN': 'finished',
    'CANC': 'finished', 'ABD': 'finished', 'AWD': 'finished', 'WO': 'finished',
}

# تحويل نوع/تفاصيل حدث API-Football إلى EVENT_TYPE_CHOICES عندنا
EVENT_TYPE_MAP = {
    'Goal': 'goal',
    'subst': 'substitution',
}


def _map_status(short_code):
    return STATUS_MAP.get(short_code, 'upcoming')


def _get_or_create_league(league_data):
    """league_data هو القسم "league" من استجابة fixture واحدة."""
    external_id = str(league_data.get('id'))
    league, _created = League.objects.get_or_create(
        external_id=external_id,
        defaults={
            'name': league_data.get('name', ''),
            'country': league_data.get('country', ''),
        },
    )
    return league


def _get_or_create_team(team_data):
    """team_data هو القسم "teams.home" أو "teams.away" من استجابة fixture."""
    external_id = str(team_data.get('id'))
    team, _created = Team.objects.get_or_create(
        external_id=external_id,
        defaults={'name': team_data.get('name', '')},
    )
    return team


def sync_fixture(fixture_data):
    """
    يُزامن مباراة واحدة (عنصر واحد من قائمة "response" في استجابة
    API-Football) — يُنشئ أو يُحدّث سجل Match المطابق محلياً.
    يُرجع كائن Match المُحدَّث، أو None إذا كانت البيانات ناقصة/غير صالحة.
    """
    fixture_info = fixture_data.get('fixture', {})
    external_id = str(fixture_info.get('id'))
    if not external_id or external_id == 'None':
        return None

    league = _get_or_create_league(fixture_data.get('league', {}))
    home_team = _get_or_create_team(fixture_data.get('teams', {}).get('home', {}))
    away_team = _get_or_create_team(fixture_data.get('teams', {}).get('away', {}))

    status_info = fixture_info.get('status', {})
    goals = fixture_data.get('goals', {})

    match_datetime = timezone.now()
    raw_date = fixture_info.get('date')
    if raw_date:
        parsed = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
        match_datetime = parsed

    match, _created = Match.objects.update_or_create(
        external_id=external_id,
        defaults={
            'league': league,
            'home_team': home_team,
            'away_team': away_team,
            'match_datetime': match_datetime,
            'status': _map_status(status_info.get('short')),
            'home_score': goals.get('home') or 0,
            'away_score': goals.get('away') or 0,
            'elapsed_minutes': status_info.get('elapsed') or 0,
        },
    )
    return match


def sync_fixture_events(match, events_data):
    """
    يُزامن أحداث مباراة واحدة (أهداف/بطاقات/تبديلات). يعتمد على تركيبة
    (المباراة + الدقيقة + اللاعب + النوع) لتفادي التكرار عند إعادة
    التشغيل، بما أن API-Football لا يُرجع معرّفاً فريداً ثابتاً لكل حدث.
    """
    synced_count = 0

    for event in events_data:
        event_type_raw = event.get('type')
        detail = event.get('detail', '')

        if event_type_raw == 'Card':
            event_type = 'red_card' if 'Red' in detail else 'yellow_card'
        else:
            event_type = EVENT_TYPE_MAP.get(event_type_raw)

        if not event_type:
            continue  # نوع حدث غير مدعوم عندنا (مثل VAR)، نتجاهله بأمان

        team_data = event.get('team', {})
        team = _get_or_create_team(team_data) if team_data else None
        if team is None:
            continue

        player_data = event.get('player') or {}
        player = None
        if player_data.get('id'):
            # نبحث فقط (لا ننشئ لاعباً جديداً هنا) — إنشاء اللاعبين مسؤولية
            # مزامنة التشكيلة/الفرق المنفصلة، وليست مزامنة الأحداث
            from core.models import Player
            player = Player.objects.filter(external_id=str(player_data['id'])).first()

        minute = event.get('time', {}).get('elapsed', 0)

        _obj, created = MatchEvent.objects.get_or_create(
            match=match, minute=minute, team=team, player=player, event_type=event_type,
            defaults={'description': detail},
        )
        if created:
            synced_count += 1

    return synced_count


def sync_today_fixtures():
    """
    نقطة الدخول الرئيسية: يجلب كل مباريات اليوم (كل البطولات) ويُزامنها.
    هذا ما يُشغَّله الأمر اليدوي (وسيصبح مهمة Celery دورية في المرحلة 2).
    """
    client = ApiFootballClient()
    today_str = timezone.now().strftime('%Y-%m-%d')

    fixtures = client.get_fixtures_by_date(today_str)

    synced_matches = []
    for fixture_data in fixtures:
        match = sync_fixture(fixture_data)
        if match:
            synced_matches.append(match)

    return synced_matches


def sync_live_fixtures_with_events():
    """
    يُزامن فقط المباريات المباشرة الآن، **مع أحداثها** (أهداف/بطاقات).
    هذا النداء أخف بكثير من sync_today_fixtures، ومُصمَّم ليُشغَّل بشكل
    متكرر جداً (كل دقيقة مثلاً في المرحلة 2 عبر Celery)، بينما
    sync_today_fixtures يكفي تشغيله كل ساعة أو يدوياً.
    """
    client = ApiFootballClient()
    live_fixtures = client.get_live_fixtures()

    results = []
    for fixture_data in live_fixtures:
        match = sync_fixture(fixture_data)
        if not match:
            continue

        try:
            events_data = client.get_fixture_events(match.external_id)
            events_synced = sync_fixture_events(match, events_data)
        except ApiFootballError as e:
            logger.warning('فشلت مزامنة أحداث المباراة %s: %s', match.id, e)
            events_synced = 0

        results.append({'match': match, 'new_events': events_synced})

    return results
