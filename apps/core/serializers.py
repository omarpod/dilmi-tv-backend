"""apps/core/serializers.py"""
from rest_framework import serializers

from apps.streaming.models import StreamSource

from .models import Channel, Match, News


class StreamSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamSource
        fields = ['url', 'label', 'priority', 'is_healthy']


class ChannelSerializer(serializers.ModelSerializer):
    # يستبدل stream_url القديم (رابط واحد) بقائمة مرتّبة — التطبيق يجرّب
    # كل رابط بالترتيب تلقائياً عند فشل الحالي (Native Failover).
    stream_sources = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['id', 'name', 'logo', 'stream_sources', 'category']

    def get_stream_sources(self, obj):
        # المسار السريع: views.py يُحمّل active_sources مسبقاً عبر
        # Prefetch(to_attr=...) لتفادي استعلام منفصل لكل قناة (N+1). إن لم
        # يكن مُحمَّلاً مسبقاً (مثال: استخدام هذا الـ Serializer من مكان
        # آخر لم يُجهّز الـ Prefetch)، نرجع لاستعلام مباشر بدل الانهيار.
        sources = getattr(obj, 'active_sources', None)
        if sources is None:
            sources = obj.sources.filter(is_active=True)
        return StreamSourceSerializer(sources, many=True).data


class MatchSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'away_team',
            'home_team_logo_url', 'away_team_logo_url',
            'competition', 'channel', 'match_datetime', 'status',
            'home_score', 'away_score', 'elapsed_minutes',
        ]


class NewsSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'image', 'source_url', 'related_match', 'created_at']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.external_image_url
