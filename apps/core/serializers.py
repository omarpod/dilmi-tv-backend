"""apps/core/serializers.py"""
from rest_framework import serializers

from .models import Channel, Match, News


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'logo', 'stream_url', 'category']


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
