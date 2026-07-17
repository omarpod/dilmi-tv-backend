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

# خلف بروكسي Railway HTTPS دائماً في الإنتاج. نُفعّل هذه فقط عندما
# DEBUG=False (محلياً على http عادي، تفعيلها يمنع تسجيل الدخول أصلاً)
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
    # unfold يجب أن يكون قبل django.contrib.admin مباشرة (شرط موثَّق
    # رسمياً من المكتبة نفسها) — يستبدل django-admin-interface بالكامل
    'unfold',
    'unfold.contrib.filters',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    # cloudinary_storage يجب أن يكون قبل django.contrib.staticfiles مباشرة
    # (شرط موثَّق رسمياً من المكتبة) — تخزين دائم للصور المرفوعة، لأن قرص
    # Railway يُمسح بالكامل عند كل عملية نشر (Ephemeral Filesystem)
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',

    'rest_framework',
    'corsheaders',

    'apps.core',
    'apps.analytics',
    'apps.dashboard',
    'apps.streaming',
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

# SSL: مطلوب دائماً على Railway (قاعدة بيانات مُدارة)، لكن غير مدعوم على
# حاوية PostgreSQL محلية عادية (docker-compose) — DATABASE_SSL_REQUIRE
# يسمح بتعطيله صراحة محلياً دون التأثير على سلوك Railway الافتراضي الآمن.
_ssl_require_override = os.environ.get('DATABASE_SSL_REQUIRE')
_ssl_require = bool(_database_url) if _ssl_require_override is None else _ssl_require_override == 'True'

DATABASES = {
    'default': dj_database_url.config(
        default=_database_url or f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
        ssl_require=_ssl_require,
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
# التخزين المؤقت (Caching) + Redis
# =============================================================================
# REDIS_URL نفسها تُستخدم لثلاثة أغراض مختلفة: Cache Framework هنا، وناقل
# مهام Celery (Broker) ومخزن نتائجها أدناه — عملية Redis واحدة تكفي الثلاثة
# جميعاً، لا حاجة لثلاث عمليات منفصلة.
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    # django-redis: ذاكرة مؤقتة *مشتركة* بين كل عمليات gunicorn (على عكس
    # LocMemCache القديمة التي كانت لكل عملية ذاكرتها المستقلة — يعني عملياً
    # أن cache_page لم يكن يعمل بفعالية حقيقية مع أكثر من Worker واحد)
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
            'TIMEOUT': 300,
        }
    }
else:
    # بدون Redis (تطوير محلي بدون Docker مثلاً) — نرجع تلقائياً لذاكرة
    # العملية الواحدة حتى لا يحتاج التطوير المحلي تشغيل Redis إجبارياً
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'dilmi-tv-cache',
            'TIMEOUT': 300,
        }
    }

# =============================================================================
# Celery — طوابير المهام (مزامنة المباريات/الأخبار + فحص روابط البث دورياً)
# =============================================================================
# بديل نهائي لحلقة run_sync_loop اليدوية: الآن Celery Beat يُشغّل نفس
# sync_data على فاصل ثابت عبر عملية worker منفصلة تماماً عن عملية الويب،
# مع دعم كامل للتوسّع الأفقي (عدة عمّال يستهلكون من نفس الطابور).
CELERY_BROKER_URL = REDIS_URL or 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = REDIS_URL or 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TIME_LIMIT = 10 * 60  # قطع أي مهمة عالقة بعد 10 دقائق بدل تعليقها للأبد

CELERY_BEAT_SCHEDULE = {
    # 'sync-live-matches' مُعطَّلة عمداً — تأكَّدنا فعلياً أن خطة RapidAPI
    # BASIC توفّر 100 طلب/شهر فقط (وليس يومياً)، وهذا لا يكفي لأي جدولة
    # منفصلة "مباشرة" مهما كان الفاصل. جدول اليوم أدناه (كل 30 دقيقة)
    # يبقى مقيّداً بحد أدنى 12 ساعة بين الطلبات الفعلية عبر
    # RAPIDAPI_MIN_CALL_INTERVAL في sync_data.py — هو المصدر الوحيد
    # المُفعَّل لبيانات RapidAPI حالياً. أعد تفعيل هذه المهمة عند ترقية
    # الخطة لحصة تدعم تحديثاً مباشراً حقيقياً:
    # 'sync-live-matches': {
    #     'task': 'apps.streaming.tasks.run_sync_live_matches',
    #     'schedule': 300.0,
    # },
    'sync-matches-and-news': {
        'task': 'apps.streaming.tasks.run_sync_data',
        'schedule': 1800.0,  # 30 دقيقة — جدول اليوم + الأخبار + التنظيف (ليس المباشر، راجع أعلاه)
    },
    'check-stream-sources-health': {
        'task': 'apps.streaming.tasks.check_stream_sources_health',
        'schedule': 45.0,  # كل 45 ثانية — فحص خفيف (HEAD) لروابطكم الخاصة فقط
    },
    'advance-match-lifecycle': {
        'task': 'apps.core.tasks.advance_match_lifecycle',
        'schedule': 60.0,  # كل دقيقة — شبكة أمان زمنية، مستقلة عن sync_data
    },
    'advance-news-lifecycle': {
        'task': 'apps.core.tasks.advance_news_lifecycle',
        'schedule': 300.0,  # كل 5 دقائق — لا حاجة لدقّة الدقيقة الواحدة هنا
    },
    'snapshot-viewers': {
        'task': 'apps.analytics.tasks.snapshot_viewers',
        'schedule': 300.0,  # كل 5 دقائق — مصدر خط اتجاه المشاهدين (Sparkline)
    },
    'prune-analytics': {
        'task': 'apps.analytics.tasks.prune_analytics',
        'schedule': 3600.0,  # كل ساعة
    },
}

# =============================================================================
# الملفات الثابتة والوسائط
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# التخزين الدائم للصور المرفوعة (Cloudinary) — بدونه، أي صورة يرفعها فريقك
# عبر /admin/ تُفقد نهائياً عند أول Deploy تالٍ لأن قرص Railway لا يُبقي أي
# شيء بين عمليات النشر. محلياً (بدون متغيرات Cloudinary) نرجع تلقائياً لتخزين
# القرص العادي حتى لا يحتاج التطوير المحلي حساب Cloudinary.
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
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

# django-cloudinary-storage يُسجّل أمر collectstatic خاصاً به بمجرد وجوده
# في INSTALLED_APPS (بغضّ النظر عن كون Cloudinary مُفعَّلاً فعلياً أم لا)،
# وهذا الأمر يقرأ STATICFILES_STORAGE القديم مباشرة كسمة خام — وهو إعداد
# لم يعد Django يُنشئه تلقائياً في Django 4.2+ عند استخدام STORAGES فقط،
# فيفشل collectstatic بالكامل بخطأ AttributeError. نُبقي هذا الإعداد
# القديم موجوداً فقط لإرضاء ذلك الفحص (STORAGES أعلاه هو المصدر الفعلي).
STATICFILES_STORAGE = STORAGES['staticfiles']['BACKEND']

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
# بدون هذا، لا تظهر أي تفاصيل عن أخطاء الـ 500 في سجلات Railway إطلاقاً:
# سلوك Django الافتراضي عند DEBUG=False يُرسل أخطاء django.request إلى
# mail_admins فقط (يتطلب SMTP مضبوطاً)، وليس إلى stdout/stderr. هذا
# يُجبر كل الأخطاء (بما فيها استثناءات قاعدة البيانات) على الظهور في
# "Deploy Logs" مباشرة، بغض النظر عن DEBUG.
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
# لم أستطع التحقق مباشرة من عمل خلاصة RSS تابعة لموقع رياضي عربي محدد
# (كووورة/يلاكورة/في الجول تحجب أدوات الجلب الآلي دون استثناء). الحل هنا
# يجمع بين مصدرين مكمّلين بدل الاعتماد على مصدر واحد:
# 1) استعلامات Google News مقيَّدة بـ site: لنفس هذه المواقع تحديداً —
#    تُرجع محتوى هذه المواقع نفسها، لكن عبر بنية تحتية موثوقة (Google
#    يزحف هو، وليس خادمنا)، فتتجاوز حجب الجلب الآلي بدل الاصطدام به.
# 2) استعلام Google News عام لكرة القدم (تنويع إضافي).
# كل خلاصة تُجلب بمعزل عن الأخرى (راجع _sync_news) — فشل واحدة لا يُسقط
# الباقي، فقط يُسجَّل تحذيراً. قابلة للاستبدال الكامل عبر متغير البيئة
# NEWS_RSS_FEED_URLS (روابط مفصولة بفواصل) دون أي تعديل على الكود.
_DEFAULT_NEWS_RSS_FEEDS = ','.join([
    'https://news.google.com/rss/search?q=site:yallakora.com&hl=ar&gl=EG&ceid=EG:ar',
    'https://news.google.com/rss/search?q=site:filgoal.com&hl=ar&gl=EG&ceid=EG:ar',
    'https://news.google.com/rss/search?q=site:kooora.com&hl=ar&gl=EG&ceid=EG:ar',
    'https://news.google.com/rss/search?q=%D9%83%D8%B1%D8%A9%20%D8%A7%D9%84%D9%82%D8%AF%D9%85&hl=ar&gl=EG&ceid=EG:ar',
])

NEWS_RSS_FEEDS = [
    url.strip()
    for url in os.environ.get('NEWS_RSS_FEED_URLS', _DEFAULT_NEWS_RSS_FEEDS).split(',')
    if url.strip()
]

# =============================================================================
# لوحة التحكم المخصصة (apps.dashboard) — منفصلة عن /admin/
# =============================================================================
LOGIN_URL = 'dashboard:login'
LOGIN_REDIRECT_URL = 'dashboard:index'

def _unfold_site_logo(request):
    """
    شعار /admin/ — يُقرأ من نفس صف SiteSettings الذي يستخدمه /dashboard/
    (راجع apps/dashboard/services.py) حتى لا يُرفع الشعار مرتين. استيراد
    النموذج هنا (داخل الدالة) عمداً وليس أعلى الملف: settings.py يُنفَّذ
    قبل تحميل تطبيقات Django، فاستيراد نموذج على مستوى الملف مباشرة يفشل.
    """
    from apps.core.models import SiteSettings

    settings_obj = SiteSettings.objects.filter(pk=1).first()
    if settings_obj and settings_obj.logo:
        return settings_obj.logo.url
    return None


# =============================================================================
# هوية لوحة التحكم (django-unfold) — يستبدل django-admin-interface بالكامل
# =============================================================================
# لوحة الألوان (COLORS) مبنية آلياً بنفس Hue/Saturation للون العلامة
# التجارية #B6FF3C عبر كل درجات Tailwind (50..950)، حتى تبقى هوية /admin/
# مطابقة تماماً لبقية المشروع (لوحة التحكم المخصصة على /dashboard/) بدل
# الاعتماد على ثيم Unfold الافتراضي المحايد.
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
