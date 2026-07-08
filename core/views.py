"""
views.py
--------
هنا نضع "المنطق": ماذا يحدث عندما يطلب تطبيق الأندرويد رابطاً معيناً؟
نستخدم ModelViewSet الذي يعطينا مجاناً:
    GET  /api/channels/       -> قائمة كل القنوات
    GET  /api/channels/1/     -> تفاصيل قناة واحدة (id=1)
(والعمليات POST/PUT/DELETE أيضاً، لكننا سنحصرها على المدير لاحقاً إذا أردت)
"""
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Channel, Team, Match, News, AdSettings
from .serializers import (
    ChannelSerializer, TeamSerializer, MatchSerializer,
    NewsSerializer, AdSettingsSerializer,
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
