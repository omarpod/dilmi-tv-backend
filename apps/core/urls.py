"""apps/core/urls.py"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AppConfigView, ChannelViewSet, MatchViewSet, NewsViewSet

router = DefaultRouter()
router.register('channels', ChannelViewSet, basename='channel')
router.register('matches', MatchViewSet, basename='match')
router.register('news', NewsViewSet, basename='news')

urlpatterns = router.urls + [
    path('app-config/', AppConfigView.as_view(), name='app-config'),
]
