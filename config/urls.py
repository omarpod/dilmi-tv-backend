"""config/urls.py"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ADMIN_SITE_HEADER/TITLE/INDEX_TITLE في settings.py مجرد قيم عادية —
# Django لا يقرأها تلقائياً، يجب ربطها يدوياً بـ admin.site هنا
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Django Administration')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Django Site Admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Administration')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),
    path('api/', include('apps.analytics.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
