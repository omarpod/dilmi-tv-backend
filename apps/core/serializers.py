"""apps/core/serializers.py"""
from rest_framework import serializers

from apps.streaming.models import StreamSource

from .models import Channel, Match, News, SiteSettings


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
            'home_score', 'away_score', 'elapsed_minutes', 'stream_url',
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


class AppConfigSerializer(serializers.ModelSerializer):
    """يُقرأ من تطبيق Flutter عند الإقلاع (/api/app-config/) — معرّفات
    شبكات الإعلانات قابلة للتغيير من الداشبورد مباشرة دون إصدار تحديث
    جديد للتطبيق."""

    class Meta:
        model = SiteSettings
        fields = [
            'ads_enabled',
            'admob_enabled', 'admob_app_id', 'admob_banner_ad_unit_id',
            'admob_interstitial_ad_unit_id', 'admob_rewarded_ad_unit_id',
            'facebook_ads_enabled', 'facebook_ads_placement_id',
            'facebook_ads_interstitial_placement_id', 'facebook_ads_rewarded_placement_id',
            'other_ads_enabled', 'other_ad_network_name',
            'other_ad_banner_id', 'other_ad_interstitial_id', 'other_ad_rewarded_id',
        ]
