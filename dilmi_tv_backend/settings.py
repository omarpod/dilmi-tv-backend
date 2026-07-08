"""
settings.py
-----------
هذا هو "مركز التحكم" في المشروع كله. كل الإعدادات العامة موجودة هنا.
"""

import os # إضافة هذه المكتبة في الأعلى مهمة
from pathlib import Path

# BASE_DIR: المسار الجذري للمشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# إعدادات الأمان
# =============================================================================
SECRET_KEY = 'django-insecure-REPLACE-THIS-KEY-BEFORE-PRODUCTION-1234567890'

DEBUG = True

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://d5c7a57daf9b5559-41-200-3-198.serveousercontent.com',
    'https://*.serveousercontent.com',
    'https://dilmi-tv-backend.onrender.com', # إضافة رابط موقعك الحقيقي
]

# =============================================================================
# التطبيقات المُفعّلة
# =============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',

    'core',
]

# =============================================================================
# الوسائط (Middleware) - تم تعديلها لإضافة WhiteNoise
# =============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # تم إضافة WhiteNoise هنا
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'dilmi_tv_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dilmi_tv_backend.wsgi.application'

# =============================================================================
# قاعدة البيانات
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# =============================================================================
# اللغة والمنطقة الزمنية
# =============================================================================
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Algiers'
USE_I18N = True
USE_TZ = True

# =============================================================================
# الملفات الثابتة (Static Files) - تم تحديثها
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# إعدادات Django REST Framework
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
