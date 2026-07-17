"""apps/core/views.py"""
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache
from rest_framework import viewsets

from apps.streaming.models import StreamSource

from .models import Channel, Match, News
from .serializers import ChannelSerializer, MatchSerializer, NewsSerializer

# يُحمَّل مسبقاً (Prefetch) مع كل قناة عبر to_attr='active_sources' — بذلك
# لا يُنفَّذ استعلام SQL منفصل لكل قناة/مباراة على حدة عند قراءة
# stream_sources في الـ Serializer (تفادي مشكلة N+1 الكلاسيكية)
_active_sources_prefetch = Prefetch(
    'sources', queryset=StreamSource.objects.filter(is_active=True), to_attr='active_sources',
)


@method_decorator(cache_page(60 * 10), name='list')  # 10 دقائق — القنوات نادراً ما تتغيّر
class ChannelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/channels/ — تخزين مؤقت لمدة 10 دقائق عبر Django Cache Framework.
    لماذا القنوات تحديداً هي الأنسب للتخزين المؤقت (وليس المباريات):
    قائمة القنوات نفسها تتغيّر نادراً جداً (إضافة قناة يدوياً من الإدارة)،
    خلافاً للمباريات التي تحتاج بيانات حيّة (نتيجة/دقيقة) في كل طلب.
    """
    queryset = Channel.objects.filter(is_active=True).prefetch_related(_active_sources_prefetch)
    serializer_class = ChannelSerializer


@method_decorator(never_cache, name='list')
class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/matches/ — بدون تخزين مؤقت عمداً: بيانات المباريات المباشرة
    (النتيجة، الدقيقة) يجب أن تكون حيّة دائماً. never_cache صريحة هنا
    (بدل الاعتماد على غياب cache_page ضمنياً) لضمان أن أي طبقة وسيطة
    (Cloudflare، بروكسي، متصفح) لا تُبقي نسخة قديمة أيضاً — وليس Django فقط.
    """
    queryset = Match.objects.select_related('channel').prefetch_related(
        Prefetch('channel__sources', queryset=StreamSource.objects.filter(is_active=True), to_attr='active_sources'),
    )
    serializer_class = MatchSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


@method_decorator(cache_page(60 * 5), name='list')  # 5 دقائق
class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/news/ — تخزين مؤقت 5 دقائق (أقصر من القنوات لأن الأخبار تتحدّث أكثر)."""
    queryset = News.objects.filter(status=News.Status.PUBLISHED)
    serializer_class = NewsSerializer
