"""
apps/core/tasks.py
--------------------
أتمتة دورة حياة المباريات والأخبار بالوقت. لهذا سلوكان مختلفان حسب مصدر
المباراة (يُميَّز عبر external_id):

1. مباريات RapidAPI (external_id مضبوط): هذه المهمة شبكة أمان فقط،
   وليست بديلاً عن sync_data.py — ذاك يبقى المصدر الأساسي والفوري لحالة
   "مباشر" (بيانات حيّة فعلية). هنا فقط نضمن أن عناصر لا تبقى عالقة
   للأبد إن تأخرت أو فشلت تلك المزامنة لفترة.

2. مباريات أُضيفت يدوياً (external_id فارغ — عبر الاستيراد الجماعي أو
   الإضافة السريعة في /dashboard/): **هذه المهمة هي المصدر الأساسي
   والوحيد** لحالتها — تحويل تلقائي كامل بالوقت وحده، بلا أي تحقق من
   مصدر خارجي فعلي (لا يوجد مصدر خارجي أصلاً لهذه المباريات). مقايضة
   مقبولة صراحة: مباراة تأخّر بدؤها الفعلي عن الموعد المُدخَل ستظهر
   "مباشرة" في وقتها المُجدوَل حتى تُصحَّح يدوياً.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .integrations.push_notifications import send_topic_notification
from .models import Match, News

logger = logging.getLogger(__name__)

# أطول مدة واقعية لمباراة (شوطان + شوط إضافي محتمل + ركلات ترجيح + هامش
# أمان) — أي مباراة تتجاوز هذا الوقت منذ موعدها المُجدوَل دون أن تُصنَّف
# "منتهية" عبر sync_data تُعتبر عالقة، وليست مباراة فعلية لا تزال جارية
LIVE_SAFETY_CUTOFF = timedelta(hours=3, minutes=30)

# مدة افتراضية لمباراة مُضافة يدوياً (شوطان + استراحة + هامش اعتيادي،
# بدون افتراض وقت إضافي/ركلات ترجيح كالحد الأعلى أعلاه) — هذه تُستخدَم
# كالحد الأساسي للانتقال لـ"منتهية"، وليست شبكة أمان فقط، لأن لا مصدر
# خارجي آخر سيصحّح الحالة لهذه المباريات على الإطلاق
MANUAL_MATCH_DURATION = timedelta(hours=2, minutes=15)


@shared_task
def advance_match_lifecycle():
    now = timezone.now()
    cutoff = now - LIVE_SAFETY_CUTOFF

    # --- مباريات RapidAPI: شبكة أمان فقط (راجع الشرح أعلى الملف) ---
    stale_upcoming = Match.objects.filter(
        status=Match.Status.UPCOMING, match_datetime__lt=cutoff, external_id__isnull=False,
    ).update(status=Match.Status.FINISHED)

    stuck_live = Match.objects.filter(
        status=Match.Status.LIVE, match_datetime__lt=cutoff, external_id__isnull=False,
    ).update(status=Match.Status.FINISHED)

    # --- مباريات مُضافة يدوياً: هذه هي الآلية الأساسية لحالتها بالكامل ---
    newly_live = list(Match.objects.filter(
        status=Match.Status.UPCOMING, match_datetime__lte=now, external_id__isnull=True,
    ))
    for match in newly_live:
        match.status = Match.Status.LIVE
        match.save(update_fields=['status', 'updated_at'])
        send_topic_notification(
            topic='match_live', title='مباشر الآن',
            body=f'{match.home_team} vs {match.away_team}',
            data={'match_id': str(match.pk)},
        )

    manual_finished = Match.objects.filter(
        status=Match.Status.LIVE,
        match_datetime__lt=now - MANUAL_MATCH_DURATION,
        external_id__isnull=True,
    ).update(status=Match.Status.FINISHED)

    manual_started = len(newly_live)

    if stale_upcoming or stuck_live or manual_started or manual_finished:
        logger.info(
            'دورة حياة المباريات: %s قادمة (RapidAPI) عالقة، %s مباشرة (RapidAPI) عالقة، '
            '%s مباراة يدوية بدأت الآن، %s مباراة يدوية انتهت.',
            stale_upcoming, stuck_live, manual_started, manual_finished,
        )

    return {
        'stale_upcoming_finished': stale_upcoming,
        'stuck_live_finished': stuck_live,
        'manual_started_live': manual_started,
        'manual_finished': manual_finished,
    }


@shared_task
def advance_news_lifecycle():
    now = timezone.now()

    published = News.objects.filter(
        status=News.Status.SCHEDULED, publish_at__isnull=False, publish_at__lte=now,
    ).update(status=News.Status.PUBLISHED)

    archived = News.objects.filter(
        status=News.Status.PUBLISHED, archive_at__isnull=False, archive_at__lte=now,
    ).update(status=News.Status.ARCHIVED)

    if published or archived:
        logger.info('دورة حياة الأخبار: %s خبر نُشر تلقائياً، %s خبر أُرشف تلقائياً.', published, archived)

    return {'published': published, 'archived': archived}
