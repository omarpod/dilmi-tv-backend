"""config/urls.py"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# هوية /admin/ (العنوان، الألوان، الأيقونة) تُضبط بالكامل عبر UNFOLD في
# settings.py — django-unfold يقرأها مباشرة، لا حاجة لربط admin.site هنا
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),
    path('api/', include('apps.analytics.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
