"""apps/core/views.py"""
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets

from .models import Channel, Match, News
from .serializers import ChannelSerializer, MatchSerializer, NewsSerializer


@method_decorator(cache_page(60 * 10), name='list')  # 10 دقائق — القنوات نادراً ما تتغيّر
class ChannelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/channels/ — تخزين مؤقت لمدة 10 دقائق عبر Django Cache Framework.
    لماذا القنوات تحديداً هي الأنسب للتخزين المؤقت (وليس المباريات):
    قائمة القنوات نفسها تتغيّر نادراً جداً (إضافة قناة يدوياً من الإدارة)،
    خلافاً للمباريات التي تحتاج بيانات حيّة (نتيجة/دقيقة) في كل طلب.
    """
    queryset = Channel.objects.filter(is_active=True)
    serializer_class = ChannelSerializer


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/matches/ — بدون تخزين مؤقت عمداً: بيانات المباريات المباشرة
    (النتيجة، الدقيقة) يجب أن تكون حيّة دائماً، والتخزين المؤقت هنا كان
    سيعرض نتيجة قديمة للمستخدم لمدة التخزين بالكامل.
    """
    queryset = Match.objects.all()
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
    queryset = News.objects.filter(is_published=True)
    serializer_class = NewsSerializer
