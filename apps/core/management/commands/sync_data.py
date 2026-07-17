"""
sync_data.py
-------------
أمر سحب البيانات (مباريات + أخبار) — مُجدوَل عبر Celery Beat (راجع
CELERY_BEAT_SCHEDULE في config/settings.py وapps/streaming/tasks.py).

يدعم وضعين، لكن أحدهما مُعطَّل من الجدولة التلقائية حالياً بسبب حصة
RapidAPI الشهرية الصغيرة جداً على خطة BASIC (100 طلب/شهر فقط — تأكَّدنا
من هذا الرقم فعلياً بعد استنفادها بالكامل):

1. `python manage.py sync_data --live-only` — المباريات المباشرة الآن
   فقط. **غير مُجدوَلة تلقائياً حالياً** — 100 طلب/شهر لا تسمح بأي فاصل
   يستحق اسم "مباشر" (حتى فاصل 12 ساعة يستهلك الحصة كاملة إن أُضيف فوق
   الوضع الثاني). تبقى متاحة للتشغيل اليدوي وقت الحاجة، مع الحماية
   الموصوفة أدناه (RAPIDAPI_MIN_CALL_INTERVAL) لمنع استنزاف الحصة بها.
2. `python manage.py sync_data` (بدون علم) — المزامنة الكاملة كل 30
   دقيقة: جدول مباريات اليوم (قادمة/منتهية، وحالتها التقريبية من نفس
   الـ Endpoint) + الأخبار (RSS، لا تستهلك حصة RapidAPI) + تنظيف
   البيانات القديمة. جزء RapidAPI منها تحديداً محكوم بحد أدنى 12 ساعة
   بين الطلبات الفعلية (RAPIDAPI_MIN_CALL_INTERVAL) بغضّ النظر عن تكرار
   جدولة Celery نفسها كل 30 دقيقة — الأخبار والتنظيف يستمران بلا تأثر.

عند ترقية خطة RapidAPI لاحقاً لحصة أكبر: ارفع RAPIDAPI_MIN_CALL_INTERVAL
هنا لفاصل أقصر يناسب الحصة الجديدة، وأعد تفعيل 'sync-live-matches' في
CELERY_BEAT_SCHEDULE إن رغبتم بتحديث مباشر حقيقي.

كلا الوضعين يُشغَّلان عبر عامل Celery (Command يُنفَّذ وينتهي فوراً،
بلا حلقة أو اتصال مفتوح) — نفس مبدأ التشغيل السابق، فقط الجدولة نفسها
انتقلت من Railway Cron/حلقة يدوية إلى Celery Beat.

== مصادر بيانات المباريات (endpoint ان اثنان مكمّلان لبعضهما) ==
1. `/football-current-live`: المباريات المباشرة الآن فقط — يُحدِّث
   النتيجة/الدقيقة لحظياً، ويُصنِّف أي مباراة اختفت منه (كانت مباشرة)
   كـ "منتهية". (--live-only)
2. `/football-get-matches-by-date`: جدول مباريات يوم كامل (بما فيها
   القادمة والمنتهية والمباشرة) — يُستخدم لتعبئة "مباريات اليوم القادمة"،
   التي لا يوفّرها Endpoint المباشر وحده. لا يُعيد تصنيف أي مباراة
   "مباشرة" حالياً في قاعدة البيانات (الأحدث/الأدق أولوية). (الوضع الكامل)

== حدود صادقة ==
حالات المباريات (status) وحقل موعد الانطلاق (kickoff) لهذا الـ Endpoint
الثاني لم يتسنَّ التحقق من تسمياتهما الدقيقة (نفس قيد الوصول لتوثيق
RapidAPI). `_classify_status` أدناه تتعامل مع أشيع التسميات المعروفة في
هذا النوع من الـ APIs، وتلجأ لمقارنة موعد الانطلاق بالوقت الحالي كحل
احتياطي إن لم تتعرّف على النص. أول تشغيل حقيقي كافٍ لتصحيحها إن احتاجت.
"""
import logging
import os
from datetime import datetime, timedelta, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime as django_parse_datetime

from apps.core.integrations.ar_translations import translate_competition, translate_team
from apps.core.integrations.push_notifications import send_topic_notification
from apps.core.integrations.rapidapi_football import fetch_live_matches, fetch_matches_by_date
from apps.core.integrations.rss_news import extract_image_url, extract_plain_text, fetch_entries
from apps.core.models import IntegrationHealth, Match, News

logger = logging.getLogger(__name__)

INTEGRATION_KEY_RAPIDAPI = 'rapidapi'
INTEGRATION_LABEL_RAPIDAPI = 'RapidAPI (بيانات المباريات)'

# بعد فشل بسبب تجاوز الحصة الشهرية (429 quota)، نتوقف عن المحاولة لهذه
# المدة قبل إعادة المحاولة تلقائياً — لا فائدة من تكرار طلب مضمون الفشل
# في كل دورة حتى تتجدّد الحصة أو تُرفَع خطة الاشتراك
QUOTA_COOLDOWN = timedelta(hours=6)

# شبكة أمان مستقلة تماماً عن جدولة Celery نفسها: خطة BASIC الحالية توفّر
# 100 طلب/شهر فقط (وليس يومياً) — حتى لو ضُبطت جدولة Celery بفاصل أقصر
# بالخطأ مستقبلاً، هذا الحد الأدنى بين الطلبات الفعلية يمنع استهلاك الحصة
# الشهرية بالكامل خلال أيام قليلة كما حدث فعلياً. عند 12 ساعة: طلبان في
# اليوم كحد أقصى = ~60 طلباً/شهر، تاركاً هامشاً (~40) للاختبار اليدوي.
RAPIDAPI_MIN_CALL_INTERVAL = timedelta(hours=12)

_UPCOMING_STATUS_HINTS = {'ns', 'not started', 'scheduled', 'upcoming', 'pre', 'tbd', 'postponed'}
_LIVE_STATUS_HINTS = {'1h', '2h', 'live', 'inplay', 'in play', 'ht', 'half time', 'et', 'p', 'pen'}
_FINISHED_STATUS_HINTS = {'ft', 'finished', 'ended', 'aet', 'match finished', 'full time'}


def _parse_kickoff(value):
    """يتعامل مع صيغ شائعة لموعد الانطلاق: نص ISO، أو Unix timestamp
    (بالثواني أو بالميلي ثانية)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 10 ** 12 else value
        try:
            return datetime.fromtimestamp(seconds, tz=dt_timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        parsed = django_parse_datetime(value)
        if parsed:
            return parsed
        if value.isdigit():
            return _parse_kickoff(int(value))
    return None


def _classify_status(status_text, kickoff_dt):
    text = str(status_text or '').strip().lower()
    if text in _UPCOMING_STATUS_HINTS:
        return Match.Status.UPCOMING
    if text in _LIVE_STATUS_HINTS:
        return Match.Status.LIVE
    if text in _FINISHED_STATUS_HINTS:
        return Match.Status.FINISHED
    if kickoff_dt:
        return Match.Status.UPCOMING if kickoff_dt > timezone.now() else Match.Status.FINISHED
    return Match.Status.UPCOMING


def _dig(data, *paths):
    """يجرّب عدة مسارات محتملة لاسم الحقل (لاختلاف التسميات بين مزوّدي
    الـ API) ويرجع أول قيمة غير فارغة يجدها. مثال: _dig(raw, 'teams.home.name', 'homeTeam')."""
    for path in paths:
        node = data
        for part in path.split('.'):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                node = None
                break
        if node not in (None, ''):
            return node
    return None


def _extract_common_fields(raw):
    """
    استخراج الحقول المشتركة بين مصدري المباريات (المباشر وجدول اليوم) —
    بما فيها ترجمة أسماء الفرق/البطولة عربياً (أفضل جهد متاح، راجع
    ar_translations.py) وروابط شعارات الفرق. يرجع None إن كانت الحقول
    الأساسية ناقصة (سجل غير قابل للاستخدام).
    """
    external_id = _dig(raw, 'id', 'fixture.id', 'matchId', 'match_id')
    home_team = _dig(raw, 'teams.home.name', 'homeTeam.name', 'homeTeam', 'home_team', 'home.name')
    away_team = _dig(raw, 'teams.away.name', 'awayTeam.name', 'awayTeam', 'away_team', 'away.name')

    if not external_id or not home_team or not away_team:
        return None

    competition_raw = _dig(raw, 'league.name', 'competition.name', 'competition', 'tournament.name')

    return {
        'external_id': str(external_id),
        'home_team': translate_team(home_team),
        'away_team': translate_team(away_team),
        'home_team_logo_url': _dig(
            raw, 'teams.home.logo', 'homeTeam.logo', 'home.logo', 'homeTeamLogo', 'homeLogo',
        ),
        'away_team_logo_url': _dig(
            raw, 'teams.away.logo', 'awayTeam.logo', 'away.logo', 'awayTeamLogo', 'awayLogo',
        ),
        # لا نُرجع سلسلة فارغة أبداً — إما اسم بطولة حقيقي (مترجم إن أمكن) أو None
        # صراحة، حتى لا يُخزَّن '' في match.competition (راجع _sync_live_matches)
        'competition': translate_competition(competition_raw) if competition_raw else None,
    }


class Command(BaseCommand):
    help = 'يسحب المباريات والأخبار من مصادر خارجية. مُجدوَل عبر Celery Beat.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--live-only', action='store_true',
            help=(
                'تحديث المباريات المباشرة فقط (سريع، بدون أخبار/جدول اليوم/'
                'تنظيف) — لتشغيله بفاصل قصير (5 دقائق حالياً) منفصل عن المزامنة '
                'الكاملة (كل 30 دقيقة).'
            ),
        )

    def handle(self, *args, **options):
        if options['live_only']:
            self._run_live_only()
        else:
            self._run_full_sync()

    def _rapidapi_quota_cooldown_remaining(self):
        """
        إن كان آخر فشل مُسجَّل لـ RapidAPI سببه تجاوز الحصة (429 quota)،
        ولا يزال ضمن فترة تهدئة قصيرة، نتخطى المحاولة الحالية كلياً بدل
        تكرار طلب مضمون الفشل كل دورة (يضيف ضجيجاً في السجلات دون أي
        فائدة، والحصة الشهرية لن تتجدّد بمجرد إعادة المحاولة على أي حال).
        يُعاد المحاولة تلقائياً بعد انتهاء فترة التهدئة — قد تكون الحصة
        تجدّدت، أو رُفعت خطة الاشتراك.
        """
        health = IntegrationHealth.objects.filter(key=INTEGRATION_KEY_RAPIDAPI).first()
        if not health or health.is_healthy or not health.last_checked_at:
            return None
        if 'quota' not in health.last_error.lower():
            return None

        remaining = QUOTA_COOLDOWN - (timezone.now() - health.last_checked_at)
        return remaining if remaining.total_seconds() > 0 else None

    def _rapidapi_min_interval_remaining(self):
        """
        شبكة أمان مستقلة عن جدولة Celery — تُحسَب من آخر *محاولة* فعلية
        (ناجحة أو فاشلة، عبر last_checked_at) بغضّ النظر عن جدول Celery
        Beat نفسه. ضرورية تحديداً هنا: خطة RapidAPI الحالية 100 طلب/شهر
        فقط (وليس يومياً) — بدون هذا الحد الأدنى، أي تشغيل يدوي متكرر
        للاختبار (كما حدث فعلياً) يستهلك الحصة الشهرية كاملة خلال أيام.
        """
        health = IntegrationHealth.objects.filter(key=INTEGRATION_KEY_RAPIDAPI).first()
        if not health or not health.last_checked_at:
            return None

        remaining = RAPIDAPI_MIN_CALL_INTERVAL - (timezone.now() - health.last_checked_at)
        return remaining if remaining.total_seconds() > 0 else None

    def _run_live_only(self):
        api_key = os.environ.get('RAPIDAPI_KEY')
        if not api_key:
            self._record_rapidapi_failure('RAPIDAPI_KEY غير مضبوط في متغيرات البيئة.')
            self.stdout.write(self.style.WARNING(
                'RAPIDAPI_KEY غير مضبوط — تم تخطي مزامنة المباريات المباشرة.'
            ))
            return

        cooldown = self._rapidapi_quota_cooldown_remaining()
        if cooldown:
            self.stdout.write(self.style.WARNING(
                f'تخطي المحاولة — الحصة الشهرية لـ RapidAPI مستنفدة على الأغلب '
                f'(سيُعاد المحاولة تلقائياً خلال {int(cooldown.total_seconds() // 60)} دقيقة).'
            ))
            return

        min_interval = self._rapidapi_min_interval_remaining()
        if min_interval:
            self.stdout.write(self.style.WARNING(
                f'تخطي المحاولة — الحد الأدنى بين طلبات RapidAPI لم يمرّ بعد '
                f'(الحصة الشهرية محدودة جداً حالياً). سيُعاد المحاولة خلال '
                f'{int(min_interval.total_seconds() // 60)} دقيقة.'
            ))
            return

        try:
            _, live_synced = self._sync_live_matches(api_key)
        except Exception as e:
            self._record_rapidapi_failure(str(e))
            logger.error('فشلت مزامنة المباريات المباشرة: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشلت مزامنة المباريات المباشرة: {e}'))
            return

        self._record_rapidapi_success()
        self.stdout.write(self.style.SUCCESS(f'تمت مزامنة {live_synced} مباراة مباشرة.'))

    def _run_full_sync(self):
        self.stdout.write('بدء المزامنة الدورية الكاملة...')

        try:
            matches_synced = self._sync_todays_fixtures()
            self.stdout.write(self.style.SUCCESS(f'تمت مزامنة {matches_synced} مباراة من جدول اليوم.'))
        except Exception as e:
            # لا نرفع الاستثناء للأعلى (sys.exit بكود خطأ) عمداً هنا —
            # فشل مصدر بيانات واحد (مثلاً API المباريات متوقف مؤقتاً)
            # لا يجب أن يمنع تشغيل مزامنة الأخبار في نفس هذا التشغيل
            logger.error('فشلت مزامنة جدول اليوم: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشلت مزامنة جدول اليوم: {e}'))

        try:
            news_synced = self._sync_news()
            self.stdout.write(self.style.SUCCESS(f'تمت إضافة {news_synced} خبر جديد.'))
        except Exception as e:
            logger.error('فشلت مزامنة الأخبار: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشلت مزامنة الأخبار: {e}'))

        try:
            self._prune_old_content()
        except Exception as e:
            logger.error('فشل تنظيف البيانات القديمة: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشل تنظيف البيانات القديمة: {e}'))

        self.stdout.write('انتهت المزامنة الكاملة.')

    def _record_rapidapi_success(self):
        IntegrationHealth.record_success(INTEGRATION_KEY_RAPIDAPI, INTEGRATION_LABEL_RAPIDAPI)

    def _record_rapidapi_failure(self, message):
        IntegrationHealth.record_failure(INTEGRATION_KEY_RAPIDAPI, INTEGRATION_LABEL_RAPIDAPI, message)

    def _prune_old_content(self):
        """
        حذف نهائي للبيانات التي لم تعد لها فائدة — وليس مسحاً كاملاً قبل
        كل مزامنة (ذاك كان سيُلغي فائدة upsert بالكامل: يُفقد التاريخ بين
        الحذف وإعادة الجلب، ويكسر عدّاد "المشاهدين المباشرين" المرتبط
        بمعرّف المباراة). بدلاً من ذلك: تنظيف دوري لِما فعلاً أصبح غير
        مفيد — مباريات انتهت منذ فترة، وأخبار قديمة — حتى لا تتراكم لوحة
        التحكم بأرقام تكبر إلى الأبد دون أن تعكس شيئاً "حالياً".
        """
        old_matches, _ = Match.objects.filter(
            status=Match.Status.FINISHED,
            match_datetime__lt=timezone.now() - timedelta(days=2),
        ).delete()

        old_news, _ = News.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=30),
        ).delete()

        if old_matches or old_news:
            self.stdout.write(
                f'تم حذف {old_matches} مباراة قديمة منتهية و{old_news} خبر قديم (تنظيف دوري).'
            )

    def _sync_todays_fixtures(self):
        """
        جدول مباريات اليوم (قادمة/منتهية/مباشرة تقريبياً عبر status
        الـ Endpoint نفسه) — المصدر الوحيد المُفعَّل حالياً لبيانات
        RapidAPI، بسبب حصة شهرية صغيرة جداً (100 طلب/شهر على خطة BASIC)
        لا تسمح بتحديث "مباشر" حقيقي مهما ضُبطت الجدولة (راجع
        RAPIDAPI_MIN_CALL_INTERVAL أعلاه، وconfig/settings.py حيث عُطِّلت
        مهمة --live-only السريعة لنفس السبب).
        """
        api_key = os.environ.get('RAPIDAPI_KEY')
        if not api_key:
            self._record_rapidapi_failure('RAPIDAPI_KEY غير مضبوط في متغيرات البيئة.')
            self.stdout.write(self.style.WARNING(
                'RAPIDAPI_KEY غير مضبوط في متغيرات البيئة — تم تخطي مزامنة المباريات.'
            ))
            return 0

        cooldown = self._rapidapi_quota_cooldown_remaining()
        if cooldown:
            self.stdout.write(self.style.WARNING(
                f'تخطي المحاولة — الحصة الشهرية لـ RapidAPI مستنفدة على الأغلب '
                f'(سيُعاد المحاولة تلقائياً خلال {int(cooldown.total_seconds() // 60)} دقيقة).'
            ))
            return 0

        min_interval = self._rapidapi_min_interval_remaining()
        if min_interval:
            self.stdout.write(self.style.WARNING(
                f'تخطي المحاولة — الحد الأدنى بين طلبات RapidAPI لم يمرّ بعد '
                f'(الحصة الشهرية محدودة جداً حالياً). سيُعاد المحاولة خلال '
                f'{int(min_interval.total_seconds() // 60)} دقيقة.'
            ))
            return 0

        try:
            # لا نُعيد تصنيف مباراة "مباشرة" بالفعل في قاعدة البيانات (حدّثتها
            # دورة --live-only الأخيرة) بحالة هذا الـ Endpoint الأقل دقة
            # للحظة الحالية — نفس الحماية التي كانت موجودة سابقاً ضمن نفس
            # التشغيل، الآن عبر قاعدة البيانات بدل نتيجة تشغيل متزامن واحد
            live_external_ids = set(
                Match.objects.filter(status=Match.Status.LIVE).values_list('external_id', flat=True)
            )
            scheduled_synced = self._sync_matches_by_date(api_key, live_external_ids)
        except Exception as e:
            self._record_rapidapi_failure(str(e))
            raise

        self._record_rapidapi_success()
        return scheduled_synced

    def _sync_live_matches(self, api_key):
        raw_matches = fetch_live_matches(api_key)

        if raw_matches:
            # تشخيصي فقط: يساعد على تصحيح أسماء الحقول أدناه إن اختلفت
            # عن المتوقع — سطر واحد خفيف لكل تشغيل، وليس البيانات كاملة
            self.stdout.write(f'حقول أول سجل خام من football-current-live: {sorted(raw_matches[0].keys())}')

        seen_external_ids = set()
        synced = 0

        for raw in raw_matches:
            fields = _extract_common_fields(raw)
            if fields is None:
                logger.warning('سجل مباراة ناقص الحقول الأساسية، تم تجاهله: %s', raw)
                continue

            external_id = fields['external_id']
            seen_external_ids.add(external_id)

            match, created = Match.objects.get_or_create(
                external_id=external_id,
                defaults={
                    'home_team': fields['home_team'],
                    'away_team': fields['away_team'],
                    # لا يوفّر هذا الـ Endpoint موعد الانطلاق الفعلي (فقط
                    # مباريات مباشرة الآن) — وقت أول رصد هو أقرب تقدير متاح،
                    # ولا نُعيد ضبطه في التحديثات اللاحقة (أسفل) حتى لا يتحرك
                    'match_datetime': timezone.now(),
                },
            )

            was_live_already = match.status == Match.Status.LIVE

            match.home_team = fields['home_team']
            match.away_team = fields['away_team']
            match.home_team_logo_url = fields['home_team_logo_url'] or match.home_team_logo_url
            match.away_team_logo_url = fields['away_team_logo_url'] or match.away_team_logo_url
            match.home_score = _dig(raw, 'goals.home', 'score.home', 'homeScore', 'home_score') or 0
            match.away_score = _dig(raw, 'goals.away', 'score.away', 'awayScore', 'away_score') or 0
            match.elapsed_minutes = _dig(raw, 'fixture.status.elapsed', 'status.elapsed', 'minute', 'time.minute') or 0
            match.competition = fields['competition'] or match.competition
            match.status = Match.Status.LIVE
            match.save()
            synced += 1

            if not was_live_already:
                # إشعار فقط عند "الانتقال" لمباشرة (وليس عند كل تحديث نتيجة
                # لمباراة مباشرة أصلاً) — وإلا لأزعجنا المستخدمين كل 15 دقيقة
                send_topic_notification(
                    topic='match_live',
                    title='مباشر الآن',
                    body=f'{fields["home_team"]} vs {fields["away_team"]}',
                    data={'match_id': external_id},
                )

        # أي مباراة كانت "مباشرة" في تشغيل سابق ولم تعد ضمن القائمة الآن
        # = انتهت فعلياً (هذا الـ Endpoint يُرجع المباريات المباشرة فقط،
        # فغيابها يعني الانتهاء لا الإلغاء أو الخطأ)
        finished = Match.objects.filter(status=Match.Status.LIVE).exclude(
            external_id__in=seen_external_ids,
        ).update(status=Match.Status.FINISHED)
        if finished:
            self.stdout.write(f'تم تصنيف {finished} مباراة كـ "منتهية" (لم تعد ضمن المباريات المباشرة).')

        return seen_external_ids, synced

    def _sync_matches_by_date(self, api_key, skip_external_ids):
        date_str = timezone.localtime(timezone.now()).strftime('%Y%m%d')
        raw_matches = fetch_matches_by_date(api_key, date_str)

        if raw_matches:
            self.stdout.write(f'حقول أول سجل خام من football-get-matches-by-date: {sorted(raw_matches[0].keys())}')

        synced = 0
        for raw in raw_matches:
            fields = _extract_common_fields(raw)
            if fields is None:
                logger.warning('سجل مباراة (جدول اليوم) ناقص الحقول الأساسية، تم تجاهله: %s', raw)
                continue

            external_id = fields['external_id']
            if external_id in skip_external_ids:
                # صُنِّفت بالفعل كـ "مباشرة" من football-current-live في نفس
                # هذا التشغيل — ذاك المصدر أدقّ للحظة الحالية، لا نُعيد تصنيفها هنا
                continue

            kickoff = _parse_kickoff(
                _dig(raw, 'fixture.timestamp', 'fixture.date', 'date', 'kickoff', 'matchDate', 'time.starting_at.timestamp')
            )
            status_text = _dig(raw, 'fixture.status.short', 'status.short', 'status', 'matchStatus')
            status = _classify_status(status_text, kickoff)

            match, created = Match.objects.get_or_create(
                external_id=external_id,
                defaults={
                    'home_team': fields['home_team'],
                    'away_team': fields['away_team'],
                    'match_datetime': kickoff or timezone.now(),
                },
            )

            match.home_team = fields['home_team']
            match.away_team = fields['away_team']
            match.home_team_logo_url = fields['home_team_logo_url'] or match.home_team_logo_url
            match.away_team_logo_url = fields['away_team_logo_url'] or match.away_team_logo_url
            match.competition = fields['competition'] or match.competition
            match.status = status
            if kickoff:
                match.match_datetime = kickoff
            if status == Match.Status.FINISHED:
                match.home_score = _dig(raw, 'goals.home', 'score.home', 'homeScore', 'home_score') or match.home_score
                match.away_score = _dig(raw, 'goals.away', 'score.away', 'awayScore', 'away_score') or match.away_score
            match.save()
            synced += 1

        return synced

    def _sync_news(self):
        from django.conf import settings

        feed_urls = getattr(settings, 'NEWS_RSS_FEEDS', [])
        if not feed_urls:
            self.stdout.write(self.style.WARNING('NEWS_RSS_FEEDS غير مضبوطة — تم تخطي مزامنة الأخبار.'))
            return 0

        created = 0
        for feed_url in feed_urls:
            try:
                entries = fetch_entries(feed_url)
            except Exception as e:
                logger.warning('فشل جلب خلاصة %s: %s', feed_url, e)
                self.stdout.write(self.style.WARNING(f'تعذّر جلب {feed_url}: {e}'))
                continue

            self.stdout.write(f'{feed_url}: {len(entries)} عنصر في الخلاصة.')

            for entry in entries:
                link = entry.get('link')
                title = entry.get('title')
                if not link or not title:
                    continue

                if News.objects.filter(source_url=link).exists():
                    continue

                content = extract_plain_text(entry) or title.strip()
                News.objects.create(
                    title=title.strip(),
                    content=content,
                    source_url=link,
                    external_image_url=extract_image_url(entry),
                )
                created += 1

        return created
