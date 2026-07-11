"""
settings.py
-----------
إعدادات المشروع المحدثة لضمان التوافق الكامل مع Railway
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-REPLACE-THIS-KEY-BEFORE-PRODUCTION-1234567890'

DEBUG = False

# تم توسيع نطاق المضيفين ليشمل Railway ولتجاوز أخطاء الـ Host Header
ALLOWED_HOSTS = [
    'web-production-d72c6.up.railway.app',
    '.railway.app',
    'localhost',
    '127.0.0.1'
]

CSRF_TRUSTED_ORIGINS = [
    'https://web-production-d72c6.up.railway.app',
]

# --- الحل الجذري للتعامل مع Proxy الخاص بـ Railway ---
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_PORT = True

# [بقيت التطبيقات والإعدادات كما هي بالضبط لضمان عدم فقدان أي ميزة]
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_ckeditor_5',
    'core',
]

# ... [تأكد من بقاء بقية ملفك كما هو (MIDDLEWARE, TEMPLATES, DATABASES, إلخ)] ...
# ... [تأكد أن JAZZMIN_SETTINGS و JAZZMIN_UI_TWEAKS في نهاية الملف] ...
