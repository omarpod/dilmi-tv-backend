"""
config/settings.py
--------------------
إعدادات Dilmi TV Backend v2 — مُهيَّأة للعمل فوراً على Railway.app.
"""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# الأمان
# =============================================================================
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-REPLACE-THIS-FOR-LOCAL-DEV-ONLY',
)

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Railway يوفّر هذا المتغير تلقائياً بنطاق خدمتك (مثال:
# your-service.up.railway.app) — نبني ALLOWED_HOSTS منه ديناميكياً
RAILWAY_PUBLIC_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN')

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = []

if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RAILWAY_PUBLIC_DOMAIN}')

_extra_hosts = os.environ.get('ADDITIONAL_ALLOWED_HOSTS', '')
for _host in filter(None, (h.strip() for h in _extra_hosts.split(','))):
    ALLOWED_HOSTS.append(_host)
    CSRF_TRUSTED_ORIGINS.append(f'https://{_host}')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =============================================================================
# التطبيقات المُفعّلة
# =============================================================================
INSTALLED_APPS = [
    # admin_interface و colorfield يجب أن يكونا قبل django.contrib.admin
    # مباشرة (شرط موثَّق رسمياً من المكتبة نفسها)
    'admin_interface',
    'colorfield',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',

    'apps.core',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

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

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# =============================================================================
# قاعدة البيانات: PostgreSQL عبر Railway (إلزامية، بدون رجوع صامت لـ SQLite)
# =============================================================================
_database_url = os.environ.get('DATABASE_URL')
_allow_local_sqlite = os.environ.get('USE_LOCAL_SQLITE', 'False') == 'True'

if not _database_url and not _allow_local_sqlite:
    raise ImproperlyConfigured(
        'DATABASE_URL غير مُعرَّف. تأكد من إضافة إضافة PostgreSQL في '
        'مشروع Railway (سيُضاف هذا المتغير تلقائياً)، أو محلياً اضبطه '
        'يدوياً، أو فعّل USE_LOCAL_SQLITE=True عمداً للتطوير بدون اتصال.'
    )

DATABASES = {
    'default': dj_database_url.config(
        default=_database_url or f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
        ssl_require=bool(_database_url),
    )
}

# =============================================================================
# اللغة والمنطقة الزمنية
# =============================================================================
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Algiers'
USE_I18N = True
USE_TZ = True

# =============================================================================
# التخزين المؤقت (Caching) — بسيط عبر Django Cache Framework
# =============================================================================
# LocMemCache: داخل عملية Python نفسها — لا يتطلب Redis. القيود (بصراحة):
# كل Worker له ذاكرته المستقلة، وتُمحى عند إعادة النشر. مقبول تماماً الآن،
# وقابل للترقية لـ django-redis لاحقاً بتغيير سطر واحد فقط.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dilmi-tv-cache',
        'TIMEOUT': 300,
    }
}

# =============================================================================
# الملفات الثابتة والوسائط
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# Django REST Framework
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# =============================================================================
# هوية لوحة التحكم (django-admin-interface)
# =============================================================================
ADMIN_SITE_HEADER = 'Dilmi TV'
ADMIN_SITE_TITLE = 'Dilmi TV'
ADMIN_INDEX_TITLE = 'إدارة الموقع'

# ألوان الثيم الافتراضي — تُضبط تلقائياً عند أول تشغيل عبر core/apps.py
# (يمكن تعديلها لاحقاً بصرياً من /admin/ نفسه عبر قسم "Themes")
DILMI_THEME_COLORS = {
    'css_header_background_color': '#0B1220',
    'css_header_text_color': '#B6FF3C',
    'css_header_link_color': '#B6FF3C',
    'css_module_background_color': '#141C2E',
    'css_module_text_color': '#FFFFFF',
    'css_module_link_color': '#B6FF3C',
    'css_generic_link_color': '#B6FF3C',
    'css_save_button_background_color': '#B6FF3C',
    'css_save_button_background_hover_color': '#8FD62E',
    'css_save_button_text_color': '#0B1220',
}
