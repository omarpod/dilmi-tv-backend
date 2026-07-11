"""
urls.py (المستوى الرئيسي للمشروع)
----------------------------------
هذا الملف هو "دليل" يوجّه كل رابط (URL) يدخل للموقع إلى الجهة المسؤولة عنه.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # /admin/  -> لوحة تحكم Django الجاهزة (لإدارة كل شيء بسهولة وبدون كود إضافي)
    path('admin/', admin.site.urls),

    # /api/  -> كل روابط الـ API الخاصة بتطبيق Dilmi TV موجودة في core/urls.py
    path('api/', include('core.urls')),

    # /ckeditor5/  -> روابط رفع الصور داخل محرر النصوص الغني (لحقل content في StaticPage)
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

# أثناء التطوير فقط: نسمح بعرض الصور المرفوعة (شعارات الفرق مثلاً) مباشرة
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
