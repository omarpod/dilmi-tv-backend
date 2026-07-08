"""
serializers.py
--------------
"Serializer" هو المسؤول عن تحويل بيانات قاعدة البيانات (Python objects)
إلى صيغة JSON التي يفهمها تطبيق الأندرويد، والعكس صحيح عند الاستقبال.

فكّر فيه كـ "مترجم" بين لغة Python ولغة JSON.
"""
from rest_framework import serializers
from .models import Channel, Team, Player, Match, LineupEntry, News, AdSettings


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        # الحقول التي ستظهر في استجابة الـ API
        fields = ['id', 'name', 'logo', 'stream_url', 'category', 'is_active', 'order']


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'name', 'shirt_number', 'position']


class TeamSerializer(serializers.ModelSerializer):
    # نضمّن قائمة اللاعبين داخل بيانات الفريق مباشرة (serializer متداخل)
    players = PlayerSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'logo', 'country', 'players']


class TeamMiniSerializer(serializers.ModelSerializer):
    """نسخة مختصرة من الفريق (بدون لاعبين) لاستخدامها داخل بيانات المباراة."""
    class Meta:
        model = Team
        fields = ['id', 'name', 'logo']


class LineupEntrySerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)

    class Meta:
        model = LineupEntry
        fields = ['id', 'player', 'is_starting']


class MatchSerializer(serializers.ModelSerializer):
    # نستبدل home_team/away_team (أرقام فقط) ببياناتها الكاملة عبر nested serializer
    home_team = TeamMiniSerializer(read_only=True)
    away_team = TeamMiniSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    lineup = LineupEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'away_team', 'channel', 'competition',
            'match_datetime', 'status', 'home_score', 'away_score', 'lineup',
        ]


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'image', 'related_match', 'published_at']


class AdSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdSettings
        fields = [
            'banner_ad_unit_id', 'interstitial_ad_unit_id',
            'banner_enabled', 'interstitial_enabled',
        ]
