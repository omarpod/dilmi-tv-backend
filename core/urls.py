"""
core/urls.py
------------
يحدد روابط الـ API الخاصة بتطبيقنا core.
DefaultRouter يُنشئ الروابط تلقائياً بناءً على الـ ViewSets (list + detail).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ChannelViewSet, TeamViewSet, MatchViewSet, NewsViewSet, ad_settings_view,
    StaticPageViewSet, track_visit_view, site_settings_view, register_fcm_token_view,
)

router = DefaultRouter()
router.register('channels', ChannelViewSet, basename='channel')
router.register('teams', TeamViewSet, basename='team')
router.register('matches', MatchViewSet, basename='match')
router.register('news', NewsViewSet, basename='news')
router.register('static-pages', StaticPageViewSet, basename='static-page')

urlpatterns = [
    # هذا يُنشئ تلقائياً:
    # /api/channels/       /api/channels/<id>/
    # /api/teams/          /api/teams/<id>/
    # /api/matches/        /api/matches/<id>/
    # /api/news/           /api/news/<id>/
    # /api/static-pages/   /api/static-pages/<slug>/   (مثال: privacy_policy، about_us)
    path('', include(router.urls)),

    # رابط مخصص لإعدادات الإعلانات: /api/ad-settings/
    path('ad-settings/', ad_settings_view, name='ad-settings'),

    # رابط مخصص لإعدادات التواصل الاجتماعي والبريد: /api/site-settings/
    path('site-settings/', site_settings_view, name='site-settings'),

    # POST لتسجيل زيارة جديدة (نظام الإحصائيات): /api/track-visit/
    path('track-visit/', track_visit_view, name='track-visit'),

    # POST لتسجيل رمز FCM لجهاز جديد (اشتراك إشعارات): /api/register-fcm-token/
    path('register-fcm-token/', register_fcm_token_view, name='register-fcm-token'),
]
