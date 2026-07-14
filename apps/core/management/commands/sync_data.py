"""
sync_data.py
-------------
أمر سحب البيانات الدوري (مباريات + أخبار) — **مُصمَّم خصيصاً ليعمل عبر
Railway Cron Job**، وليس Celery أو APScheduler.

== لماذا Railway Cron Job هو "الطريقة المثلى" التي طلبتها (وليس APScheduler) ==
1. **بلا كود إضافي للجدولة نفسها**: Railway يُشغّل هذا الأمر تلقائياً
   حسب جدول Cron تضبطه من الواجهة مباشرة — لا حاجة لأي مكتبة جدولة
   (APScheduler/Celery Beat) داخل كودك إطلاقاً.
2. **معزول تماماً عن خدمة الويب**: يعمل كخدمة Railway منفصلة (نفس
   المستودع، Start Command مختلف)، فلا يستهلك موارد Gunicorn أو يخاطر
   بتعطيل الموقع الرئيسي إن فشل.
3. **شرط إلزامي من Railway نفسه**: يجب أن **ينتهي وينهي العملية (exit)
   فور اكتمال المهمة** — Railway لا يُنهي العمليات تلقائياً؛ إن بقيت
   عملية سابقة "عالقة"، يتجاهل Railway أي تشغيل جديد مجدوَل حتى تنتهي
   الأولى. لهذا الأمر هنا يُنفّذ المهمة ثم يخرج مباشرة، دون أي حلقة
   `while True` أو اتصال مفتوح يبقيه حيّاً.

== إعداد Cron Job في Railway (خطوات) ==
1. من لوحة مشروعك على Railway: New Service → اختر نفس المستودع (Repo)
2. في إعدادات الخدمة الجديدة (وليس خدمة الويب الأصلية):
   Settings → Deploy → Custom Start Command:
       python manage.py sync_data
3. في نفس الصفحة: Settings → Cron Schedule، أدخل تعبير Cron، مثال:
       */15 * * * *     (كل 15 دقيقة — مناسب لمباريات مباشرة)
4. Settings → Variables لهذه الخدمة تحديداً: أضف RAPIDAPI_KEY، وإن أردت
   خلاصات RSS مختلفة عن الافتراضية أضف أيضاً NEWS_RSS_FEED_URLS (نفس
   القيم المستخدمة في خدمة الويب، أو انسخها من هناك).
5. Railway يُشغّل هذا تلقائياً حسب الجدول — بدون أي كود جدولة إضافي.

ملاحظة: جدولة Railway بتوقيت UTC دائماً — ضع هذا في اعتبارك عند اختيار
تكرار التشغيل.

== مصادر بيانات المباريات (endpoint ان اثنان مكمّلان لبعضهما) ==
1. `/football-current-live`: المباريات المباشرة الآن فقط — يُحدِّث
   النتيجة/الدقيقة لحظياً، ويُصنِّف أي مباراة اختفت منه (كانت مباشرة)
   كـ "منتهية".
2. `/football-get-matches-by-date`: جدول مباريات يوم كامل (بما فيها
   القادمة والمنتهية والمباشرة) — يُستخدم لتعبئة "مباريات اليوم القادمة"،
   التي لا يوفّرها Endpoint المباشر وحده. لا يُعيد تصنيف مباراة صنّفها
   Endpoint المباشر مسبقاً كـ "مباشرة" في نفس التشغيل (الأحدث/الأدق أولوية).

== حدود صادقة ==
حالات المباريات (status) وحقل موعد الانطلاق (kickoff) لهذا الـ Endpoint
الثاني لم يتسنَّ التحقق من تسمياتهما الدقيقة (نفس قيد الوصول لتوثيق
RapidAPI). `_classify_status` أدناه تتعامل مع أشيع التسميات المعروفة في
هذا النوع من الـ APIs، وتلجأ لمقارنة موعد الانطلاق بالوقت الحالي كحل
احتياطي إن لم تتعرّف على النص. أول تشغيل حقيقي كافٍ لتصحيحها إن احتاجت.
"""
import logging
import os
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime as django_parse_datetime

from apps.core.integrations.push_notifications import send_topic_notification
from apps.core.integrations.rapidapi_football import fetch_live_matches, fetch_matches_by_date
from apps.core.integrations.rss_news import extract_image_url, extract_plain_text, fetch_entries
from apps.core.models import Match, News

logger = logging.getLogger(__name__)

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


class Command(BaseCommand):
    help = 'يسحب المباريات والأخبار من مصادر خارجية. مُصمَّم للتشغيل عبر Railway Cron Job.'

    def handle(self, *args, **options):
        self.stdout.write('بدء المزامنة الدورية...')

        try:
            matches_synced = self._sync_matches()
            self.stdout.write(self.style.SUCCESS(f'تمت مزامنة {matches_synced} مباراة.'))
        except Exception as e:
            # لا نرفع الاستثناء للأعلى (sys.exit بكود خطأ) عمداً هنا —
            # فشل مصدر بيانات واحد (مثلاً API المباريات متوقف مؤقتاً)
            # لا يجب أن يمنع تشغيل مزامنة الأخبار في نفس هذا التشغيل
            logger.error('فشلت مزامنة المباريات: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشلت مزامنة المباريات: {e}'))

        try:
            news_synced = self._sync_news()
            self.stdout.write(self.style.SUCCESS(f'تمت إضافة {news_synced} خبر جديد.'))
        except Exception as e:
            logger.error('فشلت مزامنة الأخبار: %s', e, exc_info=True)
            self.stdout.write(self.style.ERROR(f'فشلت مزامنة الأخبار: {e}'))

        self.stdout.write('انتهت المزامنة — العملية ستُغلق الآن (متطلَّب من Railway Cron).')

    def _sync_matches(self):
        api_key = os.environ.get('RAPIDAPI_KEY')
        if not api_key:
            self.stdout.write(self.style.WARNING(
                'RAPIDAPI_KEY غير مضبوط في متغيرات البيئة — تم تخطي مزامنة المباريات.'
            ))
            return 0

        seen_live_ids, live_synced = self._sync_live_matches(api_key)
        scheduled_synced = self._sync_matches_by_date(api_key, seen_live_ids)
        return live_synced + scheduled_synced

    def _sync_live_matches(self, api_key):
        raw_matches = fetch_live_matches(api_key)

        if raw_matches:
            # تشخيصي فقط: يساعد على تصحيح أسماء الحقول أدناه إن اختلفت
            # عن المتوقع — سطر واحد خفيف لكل تشغيل، وليس البيانات كاملة
            self.stdout.write(f'حقول أول سجل خام من football-current-live: {sorted(raw_matches[0].keys())}')

        seen_external_ids = set()
        synced = 0

        for raw in raw_matches:
            external_id = _dig(raw, 'id', 'fixture.id', 'matchId', 'match_id')
            home_team = _dig(raw, 'teams.home.name', 'homeTeam.name', 'homeTeam', 'home_team', 'home.name')
            away_team = _dig(raw, 'teams.away.name', 'awayTeam.name', 'awayTeam', 'away_team', 'away.name')

            if not external_id or not home_team or not away_team:
                logger.warning('سجل مباراة ناقص الحقول الأساسية، تم تجاهله: %s', raw)
                continue

            external_id = str(external_id)
            seen_external_ids.add(external_id)

            match, created = Match.objects.get_or_create(
                external_id=external_id,
                defaults={
                    'home_team': home_team,
                    'away_team': away_team,
                    # لا يوفّر هذا الـ Endpoint موعد الانطلاق الفعلي (فقط
                    # مباريات مباشرة الآن) — وقت أول رصد هو أقرب تقدير متاح،
                    # ولا نُعيد ضبطه في التحديثات اللاحقة (أسفل) حتى لا يتحرك
                    'match_datetime': timezone.now(),
                },
            )

            was_live_already = match.status == Match.Status.LIVE

            match.home_team = home_team
            match.away_team = away_team
            match.home_score = _dig(raw, 'goals.home', 'score.home', 'homeScore', 'home_score') or 0
            match.away_score = _dig(raw, 'goals.away', 'score.away', 'awayScore', 'away_score') or 0
            match.elapsed_minutes = _dig(raw, 'fixture.status.elapsed', 'status.elapsed', 'minute', 'time.minute') or 0
            match.competition = _dig(raw, 'league.name', 'competition.name', 'competition', 'tournament.name') or match.competition
            match.status = Match.Status.LIVE
            match.save()
            synced += 1

            if not was_live_already:
                # إشعار فقط عند "الانتقال" لمباشرة (وليس عند كل تحديث نتيجة
                # لمباراة مباشرة أصلاً) — وإلا لأزعجنا المستخدمين كل 15 دقيقة
                send_topic_notification(
                    topic='match_live',
                    title='مباشر الآن',
                    body=f'{home_team} vs {away_team}',
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
            external_id = _dig(raw, 'id', 'fixture.id', 'matchId', 'match_id')
            home_team = _dig(raw, 'teams.home.name', 'homeTeam.name', 'homeTeam', 'home_team', 'home.name')
            away_team = _dig(raw, 'teams.away.name', 'awayTeam.name', 'awayTeam', 'away_team', 'away.name')

            if not external_id or not home_team or not away_team:
                logger.warning('سجل مباراة (جدول اليوم) ناقص الحقول الأساسية، تم تجاهله: %s', raw)
                continue

            external_id = str(external_id)
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
                    'home_team': home_team,
                    'away_team': away_team,
                    'match_datetime': kickoff or timezone.now(),
                },
            )

            match.home_team = home_team
            match.away_team = away_team
            match.competition = _dig(raw, 'league.name', 'competition.name', 'competition', 'tournament.name') or match.competition
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
