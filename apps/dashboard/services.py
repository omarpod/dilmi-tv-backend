"""
apps/dashboard/services.py
-----------------------------
منطق تجميع بيانات لوحة التحكم — مفصول عن views.py حتى تبقى الـ view بسيطة
(تستدعي دالة واحدة وتُمرّر النتيجة للقالب)، ولأن حساب "نسبة التفاعل" و
رسم الدونات منطق مستقل تماماً عن دورة حياة طلب HTTP.
"""
from datetime import timedelta

from django.db.models import Count, Max
from django.utils import timezone

from apps.analytics.models import Platform, ViewerSession, ViewerSnapshot
from apps.core.models import Channel, Match, News

LIVE_THRESHOLD_SECONDS = 90

PLATFORM_COLORS = {
    'phone': '#B6FF3C',
    'tablet': '#4DE1FF',
    'tv': '#FF6EC7',
    'web': '#FFD166',
    'other': '#93A2C0',
}


def get_dashboard_context():
    now = timezone.now()
    live_threshold = now - timedelta(seconds=LIVE_THRESHOLD_SECONDS)

    current_live_viewers = ViewerSession.objects.filter(last_seen__gte=live_threshold).count()

    peak_24h = ViewerSnapshot.objects.filter(
        taken_at__gte=now - timedelta(hours=24),
    ).aggregate(peak=Max('live_viewers'))['peak'] or 0
    engagement_pct = round((current_live_viewers / peak_24h) * 100) if peak_24h else None

    unique_devices_today = (
        ViewerSession.objects.filter(last_seen__date=now.date())
        .values('device_id').distinct().count()
    )

    sparkline_values = list(
        ViewerSnapshot.objects.order_by('-taken_at')[:12].values_list('live_viewers', flat=True)
    )[::-1]

    live_matches = list(
        Match.objects.filter(status='live')
        .select_related('channel')
        .order_by('-elapsed_minutes')
    )
    for match in live_matches:
        match.live_viewers = match.viewer_sessions.filter(last_seen__gte=live_threshold).count()

    upcoming_matches = list(
        Match.objects.filter(status='upcoming')
        .select_related('channel')
        .order_by('match_datetime')[:6]
    )

    return {
        'stats': {
            'current_live_viewers': current_live_viewers,
            'total_matches': Match.objects.count(),
            'live_now': len(live_matches),
            'active_channels': Channel.objects.filter(is_active=True).count(),
            'published_news': News.objects.filter(is_published=True).count(),
            'unique_devices_today': unique_devices_today,
            'engagement_pct': engagement_pct,
        },
        'sparkline': _build_sparkline_svg(sparkline_values),
        'live_matches': live_matches,
        'upcoming_matches': upcoming_matches,
        'donut': _build_donut(live_threshold),
        'site_logo_url': _get_site_logo_url(),
    }


def _get_site_logo_url():
    """
    مصدر الشعار الموحّد بين /admin/ و/dashboard/: نفس الشعار الذي يُرفع من
    /admin/core/sitesettings/ — بدون تكرار آلية رفع صور منفصلة لكل واجهة.
    """
    from apps.core.models import SiteSettings

    settings_obj = SiteSettings.objects.filter(pk=1).first()
    if settings_obj and settings_obj.logo:
        return settings_obj.logo.url
    return None


def _build_sparkline_svg(values, width=180, height=40):
    """يبني Sparkline كـ SVG بسيط بدون أي مكتبة JS — إن لم تتوفر بيانات كافية بعد
    (Railway Cron الخاص بـ snapshot_viewers لم يُشغَّل بعد)، يرجع خطاً مسطحاً."""
    if len(values) < 2:
        values = [0, 0]

    highest = max(values) or 1
    step = width / (len(values) - 1)
    points = [
        f'{i * step:.1f},{height - (v / highest) * (height - 4) - 2:.1f}'
        for i, v in enumerate(values)
    ]
    return {'points': ' '.join(points), 'width': width, 'height': height}


def _build_donut(live_threshold):
    breakdown = list(
        ViewerSession.objects.filter(last_seen__gte=live_threshold)
        .values('platform').annotate(count=Count('id')).order_by('-count')
    )
    total = sum(row['count'] for row in breakdown)

    if not total:
        return {'gradient': '#24304a 0% 100%', 'legend': [], 'total': 0}

    segments = []
    legend = []
    cursor = 0.0
    for row in breakdown:
        pct = row['count'] / total * 100
        color = PLATFORM_COLORS.get(row['platform'], PLATFORM_COLORS['other'])
        segments.append(f'{color} {cursor:.2f}% {cursor + pct:.2f}%')
        legend.append({
            'label': Platform(row['platform']).label,
            'count': row['count'],
            'pct': round(pct),
            'color': color,
        })
        cursor += pct

    return {'gradient': ', '.join(segments), 'legend': legend, 'total': total}
