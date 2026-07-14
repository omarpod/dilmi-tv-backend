"""apps/analytics/serializers.py"""
from rest_framework import serializers

from .models import ViewerSession


class HeartbeatSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=64)
    platform = serializers.ChoiceField(choices=ViewerSession._meta.get_field('platform').choices, required=False, default='other')
    channel_id = serializers.UUIDField(required=False, allow_null=True)
    match_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get('channel_id') and not attrs.get('match_id'):
            raise serializers.ValidationError('يجب توفير channel_id أو match_id على الأقل.')
        return attrs
