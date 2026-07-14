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

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# =============================================================================
# التطبيقات المُفعّلة
# =============================================================================
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',

    'rest_framework',
    'corsheaders',

    'apps.core',
    'apps.analytics',
    'apps.dashboard',
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
# قاعدة البيانات
# =============================================================================
_database_url = os.environ.get('DATABASE_URL')
_allow_local_sqlite = os.environ.get('USE_LOCAL_SQLITE', 'False') == 'True'

if not _database_url and not _allow_local_sqlite:
    raise ImproperlyConfigured(
        'DATABASE_URL غير مُعرَّف.'
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
# التخزين المؤقت (Caching)
# =============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dilmi-tv-cache',
        'TIMEOUT': 300,
    }
}

# =============================================================================
# الملفات الثابتة والوسائط (تم التعديل هنا)
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

_cloudinary_configured = bool(os.environ.get('CLOUDINARY_CLOUD_NAME'))

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'
        if _cloudinary_configured
        else 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    },
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
# التسجيل (Logging)
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# =============================================================================
# مصادر أخبار sync_data (RSS)
# =============================================================================
_DEFAULT_NEWS_RSS_FEEDS = 'https://news.google.com/rss/search?q=%D9%83%D8%B1%D8%A9%20%D8%A7%D9%84%D9%82%D8%AF%D9%85&hl=ar&gl=EG&ceid=EG:ar'

NEWS_RSS_FEEDS = [
    url.strip()
    for url in os.environ.get('NEWS_RSS_FEED_URLS', _DEFAULT_NEWS_RSS_FEEDS).split(',')
    if url.strip()
]

# =============================================================================
# لوحة التحكم
# =============================================================================
LOGIN_URL = 'dashboard:login'
LOGIN_REDIRECT_URL = 'dashboard:index'

def _unfold_site_logo(request):
    from apps.core.models import SiteSettings
    settings_obj = SiteSettings.objects.filter(pk=1).first()
    if settings_obj and settings_obj.logo:
        return settings_obj.logo.url
    return None

UNFOLD = {
    'SITE_TITLE': 'Dilmi TV',
    'SITE_HEADER': 'Dilmi TV',
    'SITE_LOGO': _unfold_site_logo,
    'SITE_SYMBOL': 'sports_soccer',
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': False,
    'COLORS': {
        'primary': {
            '50': '249 255 240',
            '100': '242 255 219',
            '200': '228 255 184',
            '300': '213 255 143',
            '400': '194 255 92',
            '500': '182 255 60',
            '600': '149 238 0',
            '700': '108 172 0',
            '800': '69 111 0',
            '900': '38 60 0',
            '950': '19 31 0',
        },
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': True,
    },
}
