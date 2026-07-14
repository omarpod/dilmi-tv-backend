"""apps/core/urls.py"""
from rest_framework.routers import DefaultRouter

from .views import ChannelViewSet, MatchViewSet, NewsViewSet

router = DefaultRouter()
router.register('channels', ChannelViewSet, basename='channel')
router.register('matches', MatchViewSet, basename='match')
router.register('news', NewsViewSet, basename='news')

urlpatterns = router.urls
