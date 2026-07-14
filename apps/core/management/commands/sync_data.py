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
4. Settings → Variables لهذه الخدمة تحديداً: أضف RAPIDAPI_KEY (نفس
   القيمة المستخدمة في خدمة الويب، أو انسخها من هناك).
5. Railway يُشغّل هذا تلقائياً حسب الجدول — بدون أي كود جدولة إضافي.

ملاحظة: جدولة Railway بتوقيت UTC دائماً — ضع هذا في اعتبارك عند اختيار
تكرار التشغيل.

== حدود مصدر بيانات المباريات الحالي (مهم) ==
Endpoint المُزوَّد (`/football-current-live`) يُرجع **المباريات المباشرة
فقط** — لا يحتوي جدول مباريات اليوم القادمة. لذلك هذا الأمر قادر على:
  - تصنيف مباراة كـ "مباشرة" (موجودة في الاستجابة الآن).
  - تصنيف مباراة كانت مباشرة كـ "منتهية" (اختفت من الاستجابة).
لكنه **لا يستطيع** تعبئة "مباريات اليوم القادمة" تلقائياً — هذه تحتاج
Endpoint آخر للجدول الزمني (Fixtures/Schedule) من نفس المزوّد أو غيره؛
حتى ذلك، تُضاف يدوياً من /admin/ أو /dashboard/.
"""
import logging
import os

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.integrations.rapidapi_football import fetch_live_matches
from apps.core.models import Match

logger = logging.getLogger(__name__)


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

        raw_matches = fetch_live_matches(api_key)

        if raw_matches:
            # تشخيصي فقط: يساعد على تصحيح أسماء الحقول أدناه إن اختلفت
            # عن المتوقع — سطر واحد خفيف لكل تشغيل، وليس البيانات كاملة
            self.stdout.write(f'حقول أول سجل خام من الـ API: {sorted(raw_matches[0].keys())}')

        seen_external_ids = []
        synced = 0

        for raw in raw_matches:
            external_id = _dig(raw, 'id', 'fixture.id', 'matchId', 'match_id')
            home_team = _dig(raw, 'teams.home.name', 'homeTeam.name', 'homeTeam', 'home_team', 'home.name')
            away_team = _dig(raw, 'teams.away.name', 'awayTeam.name', 'awayTeam', 'away_team', 'away.name')

            if not external_id or not home_team or not away_team:
                logger.warning('سجل مباراة ناقص الحقول الأساسية، تم تجاهله: %s', raw)
                continue

            external_id = str(external_id)
            seen_external_ids.append(external_id)

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

            match.home_team = home_team
            match.away_team = away_team
            match.home_score = _dig(raw, 'goals.home', 'score.home', 'homeScore', 'home_score') or 0
            match.away_score = _dig(raw, 'goals.away', 'score.away', 'awayScore', 'away_score') or 0
            match.elapsed_minutes = _dig(raw, 'fixture.status.elapsed', 'status.elapsed', 'minute', 'time.minute') or 0
            match.competition = _dig(raw, 'league.name', 'competition.name', 'competition', 'tournament.name') or match.competition
            match.status = Match.Status.LIVE
            match.save()
            synced += 1

        # أي مباراة كانت "مباشرة" في تشغيل سابق ولم تعد ضمن القائمة الآن
        # = انتهت فعلياً (هذا الـ Endpoint يُرجع المباريات المباشرة فقط،
        # فغيابها يعني الانتهاء لا الإلغاء أو الخطأ)
        finished = Match.objects.filter(status=Match.Status.LIVE).exclude(
            external_id__in=seen_external_ids,
        ).update(status=Match.Status.FINISHED)
        if finished:
            self.stdout.write(f'تم تصنيف {finished} مباراة كـ "منتهية" (لم تعد ضمن المباريات المباشرة).')

        return synced

    def _sync_news(self):
        """اربط هنا استدعاء rss_news_sync (نفس الملف من المشروع القديم قابل للنقل مباشرة)."""
        return 0
