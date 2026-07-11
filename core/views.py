"""
views.py
--------
هنا نضع "المنطق": ماذا يحدث عندما يطلب تطبيق الأندرويد رابطاً معيناً؟
نستخدم ModelViewSet الذي يعطينا مجاناً:
    GET  /api/channels/       -> قائمة كل القنوات
    GET  /api/channels/1/     -> تفاصيل قناة واحدة (id=1)
(والعمليات POST/PUT/DELETE أيضاً، لكننا سنحصرها على المدير لاحقاً إذا أردت)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Channel, Team, Match, News, AdSettings,
    Analytics, SiteSettings, NotificationSubscriber, StaticPage,
)
from .serializers import (
    ChannelSerializer, TeamSerializer, MatchSerializer,
    NewsSerializer, AdSettingsSerializer,
    AnalyticsSerializer, SiteSettingsSerializer,
    NotificationSubscriberSerializer, StaticPageSerializer,
)


class ChannelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnlyModelViewSet = يسمح فقط بالقراءة (GET) من التطبيق.
    الإضافة/التعديل/الحذف تتم فقط من لوحة تحكم /admin (لأمان أكبر).
    """
    # نعرض فقط القنوات المفعّلة، مرتبة حسب "ترتيب الظهور"
    queryset = Channel.objects.filter(is_active=True).order_by('order')
    serializer_class = ChannelSerializer


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Match.objects.all().select_related('home_team', 'away_team', 'channel')
    serializer_class = MatchSerializer

    def get_queryset(self):
        """
        يسمح بالتصفية عبر الرابط، مثال:
        /api/matches/?status=live   -> يعرض فقط المباريات المباشرة الآن
        """
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = News.objects.filter(is_published=True)
    serializer_class = NewsSerializer


@api_view(['GET'])
def ad_settings_view(request):
    """
    رابط مخصص وبسيط (وليس ViewSet كامل) لأن إعدادات الإعلانات سجل واحد فقط.
    الرابط: /api/ad-settings/
    """
    settings_obj, _created = AdSettings.objects.get_or_create(pk=1)
    serializer = AdSettingsSerializer(settings_obj)
    return Response(serializer.data)


def _get_client_ip(request):
    """
    يستخرج عنوان IP الحقيقي للزائر من الطلب. يتحقق أولاً من ترويسة
    X-Forwarded-For (يستخدمها Render وغيره من مزودي الاستضافة خلف بروكسي)
    قبل اللجوء للعنوان المباشر، وإلا سنسجّل دائماً IP خادم Render الداخلي
    بدل IP المستخدم الفعلي.
    """
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        # قد تحتوي الترويسة عدة عناوين مفصولة بفاصلة، الأول هو عنوان الزائر الحقيقي
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@api_view(['POST'])
def track_visit_view(request):
    """
    رابط "نظام الإحصائيات": يستدعيه تطبيق Flutter في كل مرة يُفتح فيها
    التطبيق أو يزور فيها المستخدم شاشة مهمة، لتسجيل زيارة جديدة.
    الرابط: POST /api/track-visit/
    الحقول المتوقعة في الطلب: device (اختياري)، screen (اختياري)
    """
    device = request.data.get('device', '')
    screen = request.data.get('screen', '')

    Analytics.objects.create(
        ip_address=_get_client_ip(request),
        device=device,
        screen=screen,
    )
    # نُرجع 201 Created بدون بيانات إضافية؛ التطبيق لا يحتاج قراءة أي شيء هنا
    return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
def site_settings_view(request):
    """رابط إعدادات التواصل الاجتماعي والبريد. الرابط: /api/site-settings/"""
    settings_obj, _created = SiteSettings.objects.get_or_create(pk=1)
    serializer = SiteSettingsSerializer(settings_obj)
    return Response(serializer.data)


@api_view(['POST'])
def register_fcm_token_view(request):
    """
    يستدعيه التطبيق مرة عند أول تشغيل (وكلما تغيّر رمز FCM) لتسجيل الجهاز
    كمشترك بالإشعارات. الرابط: POST /api/register-fcm-token/
    الحقول المتوقعة: fcm_token (إلزامي)، device_platform (اختياري، افتراضي android)
    """
    serializer = NotificationSubscriberSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class StaticPageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    يوفر صفحات "سياسة الخصوصية" و"من نحن".
    lookup_field='slug' يعني أن الرابط يستخدم الاسم النصي بدل الرقم:
        GET /api/static-pages/privacy_policy/
        GET /api/static-pages/about_us/
    بدل GET /api/static-pages/1/ (أوضح بكثير لتطبيق Flutter).
    """
    queryset = StaticPage.objects.all()
    serializer_class = StaticPageSerializer
    lookup_field = 'slug'
