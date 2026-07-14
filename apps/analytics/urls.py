"""apps/analytics/urls.py"""
from django.urls import path

from .views import HeartbeatView

urlpatterns = [
    path('viewers/heartbeat/', HeartbeatView.as_view(), name='viewer-heartbeat'),
]
