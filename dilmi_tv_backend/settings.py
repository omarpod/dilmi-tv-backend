"""
settings.py
-----------
مركز التحكم المحدث للمشروع - تم ضبط إعدادات الأمان لـ Railway.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-REPLACE-THIS-KEY-BEFORE-PRODUCTION-1234567890'

# تم ضبطه على False للإنتاج لضمان الأمان وعدم كشف تفاصيل الخطأ
DEBUG = False

# الحل الحاسم لخطأ Bad Request (400): إضافة النقطة في البداية يسمح بكل النطاقات الفرعية على Railway
ALLOWED_HOSTS = [
    'web-production-d72c6.up.railway.app',
    '.railway.app',
    'localhost',
    '127.0.0.1'
]

# CSRF_TRUSTED_ORIGINS يجب أن يحتوي على الرابط الكامل فقط
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-d72c6.up.railway.app',
]

# بقية التطبيقات والإعدادات (تم الحفاظ عليها كما هي)
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

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# [بقية الإعدادات الخاصة بـ Jazzmin و StaticFiles التي أرفقتها تبقى كما هي في ملفك]
# تأكد فقط من الاحتفاظ بـ JAZZMIN_SETTINGS و JAZZMIN_UI_TWEAKS في نهاية الملف.
