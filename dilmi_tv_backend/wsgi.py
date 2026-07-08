"""
wsgi.py
-------
ملف قياسي يستخدمه خادم الإنتاج (مثل gunicorn) لتشغيل تطبيق Django.
لا تحتاج لتعديل هذا الملف عادةً.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dilmi_tv_backend.settings')

application = get_wsgi_application()
