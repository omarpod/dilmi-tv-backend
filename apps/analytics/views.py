"""apps/analytics/views.py"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ViewerSession
from .serializers import HeartbeatSerializer


class HeartbeatView(APIView):
    """
    POST /api/viewers/heartbeat/
    يستدعيها تطبيق العميل كل 30 ثانية تقريباً أثناء تشغيل بث — بدون
    استدعاءات فعلية من العميل، يبقى عدد "المشاهدين الآن" صفراً بصدق.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = HeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ViewerSession.objects.update_or_create(
            device_id=data['device_id'],
            channel_id=data.get('channel_id'),
            match_id=data.get('match_id'),
            defaults={'platform': data.get('platform', 'other')},
        )
        return Response({'ok': True})
