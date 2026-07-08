"""
core/urls.py
------------
يحدد روابط الـ API الخاصة بتطبيقنا core.
DefaultRouter يُنشئ الروابط تلقائياً بناءً على الـ ViewSets (list + detail).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ChannelViewSet, TeamViewSet, MatchViewSet, NewsViewSet, ad_settings_view

router = DefaultRouter()
router.register('channels', ChannelViewSet, basename='channel')
router.register('teams', TeamViewSet, basename='team')
router.register('matches', MatchViewSet, basename='match')
router.register('news', NewsViewSet, basename='news')

urlpatterns = [
    # هذا يُنشئ تلقائياً:
    # /api/channels/   /api/channels/<id>/
    # /api/teams/      /api/teams/<id>/
    # /api/matches/    /api/matches/<id>/
    # /api/news/       /api/news/<id>/
    path('', include(router.urls)),

    # رابط مخصص لإعدادات الإعلانات: /api/ad-settings/
    path('ad-settings/', ad_settings_view, name='ad-settings'),
]
