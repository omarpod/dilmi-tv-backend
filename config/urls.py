"""config/urls.py"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.core.views import app_ads_txt

# هوية /admin/ (العنوان، الألوان، الأيقونة) تُضبط بالكامل عبر UNFOLD في
# settings.py — django-unfold يقرأها مباشرة، لا حاجة لربط admin.site هنا
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),
    path('api/', include('apps.analytics.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    # يجب أن يبقى في جذر النطاق (وليس داخل apps.core.urls تحت /api/) —
    # راجع apps/core/views.py: app_ads_txt لسبب ذلك
    path('app-ads.txt', app_ads_txt, name='app-ads-txt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
