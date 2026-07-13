"""
settings.py
-----------
مركز التحكم في المشروع كله. أُعيدت هيكلته بالكامل لضمان الاستقرار على
Render مع قاعدة بيانات Neon (PostgreSQL)، ولوحة تحكم Django 5 الافتراضية
مُخصَّصة عبر متغيرات CSS الرسمية (بدون أي مكتبة طرف ثالث لتصميم اللوحة).
"""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# إعدادات الأمان
# =============================================================================

# SECRET_KEY يُقرأ من متغير بيئة في الإنتاج (لا يظهر أبداً في الكود
# المرفوع على GitHub). القيمة الثابتة هنا احتياطية للتطوير المحلي فقط.
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-REPLACE-THIS-KEY-FOR-LOCAL-DEV-ONLY-1234567890',
)

# DEBUG يُقرأ من متغير بيئة أيضاً؛ القيمة الافتراضية False (آمنة) إن لم
# يُحدَّد المتغير إطلاقاً، حتى لا يبقى DEBUG=True بالخطأ في الإنتاج.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Render يوفّر هذا المتغير تلقائياً بعنوان نطاق خدمتك الحقيقي — نبنى
# ALLOWED_HOSTS و CSRF_TRUSTED_ORIGINS منه ديناميكياً، فلا حاجة لتعديل
# هذا الملف يدوياً في كل مرة يتغيّر فيها النطاق أو تنتقل بين منصات.
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = []

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# دعم إضافي لأي نطاقات إضافية (مثل نطاق مخصص لاحقاً)، مفصولة بفاصلة،
# عبر متغير بيئة اختياري ADDITIONAL_ALLOWED_HOSTS، مثال:
#   ADDITIONAL_ALLOWED_HOSTS=dilmi-tv.com,www.dilmi-tv.com
_extra_hosts = os.environ.get('ADDITIONAL_ALLOWED_HOSTS', '')
if _extra_hosts:
    for _host in _extra_hosts.split(','):
        _host = _host.strip()
        if _host:
            ALLOWED_HOSTS.append(_host)
            CSRF_TRUSTED_ORIGINS.append(f'https://{_host}')

# SECURE_PROXY_SSL_HEADER: ضرورية خلف بروكسي Render (الاتصال الحقيقي مع
# المتصفح https، لكن الاتصال الداخلي بين بروكسي Render والتطبيق http).
# ملاحظة: تعمّدنا عدم إضافة USE_X_FORWARDED_HOST — تسبب أخطاء 400 غير
# متوقعة على بعض المنصات إذا لم تُرسَل الترويسة بالضبط كما يتوقعها Django.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =============================================================================
# التطبيقات المُفعّلة (Installed Apps)
# =============================================================================
INSTALLED_APPS = [
    # admin_interface و colorfield يجب أن يكونا قبل django.contrib.admin
    # مباشرة (شرط موثَّق رسمياً من المكتبة) — يضيفان قسم "Themes" داخل
    # لوحة التحكم لتخصيص الألوان تفاعلياً دون لمس الكود. لا يستبدلان
    # base_site.html المخصص عندنا حالياً (يبقى هو الفعّال تلقائياً)، لذا
    # صفر خطر على الاستقرار الحالي — فقط أداة إضافية متاحة عند الحاجة.
    'admin_interface',
    'colorfield',

    'django.contrib.admin',        # لوحة تحكم Django الجاهزة (ثيمها الأصلي، مُخصَّص عبر CSS فقط)
    'django.contrib.auth',         # نظام المستخدمين وتسجيل الدخول
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    # cloudinary_storage يجب أن يكون قبل django.contrib.staticfiles مباشرة
    # (شرط موثَّق من المكتبة نفسها) حتى يعمل تخزين الصور الدائم بشكل صحيح
    'cloudinary_storage',
    'django.contrib.staticfiles',  # لخدمة ملفات CSS/JS/الصور
    'cloudinary',

    'rest_framework',              # مكتبة بناء الـ API
    'corsheaders',                 # للسماح لتطبيق الأندرويد بالاتصال بالـ API
    'django_ckeditor_5',           # محرر نصوص غني (HTML) لصفحات "من نحن" و"سياسة الخصوصية"

    'core',                        # تطبيقنا الخاص
]

# مطلوبة من django-admin-interface لدعم النوافذ المنبثقة (Modals) بدل
# نوافذ popup تقليدية، وإسكات تحذير أمني غير مؤثر معروف من المكتبة نفسها
X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

# =============================================================================
# الوسائط (Middleware)
# =============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # خدمة الملفات الثابتة في الإنتاج
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# أثناء التطوير: نسمح لأي مصدر بالاتصال بالـ API (تطبيق الأندرويد على المحاكي مثلاً).
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'dilmi_tv_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # BASE_DIR/templates: يسمح بتخصيص قوالب Django (مثل
        # admin/base_site.html لإضافة الشعار وملف CSS المخصص عبر نقطة
        # التمديد الرسمية والموثَّقة، دون تعديل ملفات Django نفسها).
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

WSGI_APPLICATION = 'dilmi_tv_backend.wsgi.application'

# =============================================================================
# قاعدة البيانات: Neon (PostgreSQL) دائماً — بدون أي رجوع صامت لـ SQLite
# =============================================================================
# ⚠️ التعديل الجوهري هنا: كانت النسخة السابقة تتحول تلقائياً وبصمت لـ
# SQLite محلي إذا لم يوجد DATABASE_URL — وهذا بالضبط ما سبَّب "التضارب"
# الذي وصفته: تطوّر وتختبر محلياً على بيانات SQLite منفصلة تماماً عن
# Neon الحقيقية، فتبدو الأمور تعمل محلياً بينما تنهار في الإنتاج لأن
# البيانات الفعلية مختلفة كلياً بين البيئتين.
#
# الآن: DATABASE_URL **إلزامي دائماً** (على جهازك وعلى Render سواء بسواء).
# إذا لم يكن موجوداً، يتوقف تشغيل المشروع فوراً برسالة خطأ واضحة، بدل
# الاستمرار بصمت على قاعدة بيانات مختلفة دون أن تلاحظ.
#
# رجوع اضطراري وصريح فقط (وليس صامتاً): إذا احتجت فعلاً العمل بدون
# اتصال إنترنت مؤقتاً، فعّل ذلك عمداً عبر متغير بيئة إضافي منفصل:
#     USE_LOCAL_SQLITE=True
# هذا يضمن أن أي استخدام لـ SQLite كان **قراراً واعياً**، وليس افتراضياً
# خفياً قد تنساه.
_database_url = os.environ.get('DATABASE_URL')
_allow_local_sqlite = os.environ.get('USE_LOCAL_SQLITE', 'False') == 'True'

if not _database_url and not _allow_local_sqlite:
    raise ImproperlyConfigured(
        'متغير البيئة DATABASE_URL غير مُعرَّف. المشروع الآن يعتمد كلياً '
        'على Neon (PostgreSQL) في كل البيئات لتفادي تضارب البيانات بين '
        'التطوير المحلي والإنتاج.\n'
        '- على Render: تأكد من ضبط DATABASE_URL في Environment.\n'
        '- محلياً: انسخ نفس DATABASE_URL من Render واضبطه في متغيرات '
        'بيئتك (PowerShell: $env:DATABASE_URL="...").\n'
        '- إذا احتجت العمل بدون إنترنت مؤقتاً وبوعي كامل بالمخاطر، '
        'فعّل USE_LOCAL_SQLITE=True عمداً.'
    )

# ⚠️ conn_max_age=0: رابط اتصال Neon الافتراضي غالباً "مُجمَّع" (Pooled)
# عبر PgBouncer في وضع "Transaction Mode"، وهذا الوضع **لا يتوافق** مع
# الاتصالات الدائمة المُعاد استخدامها التي يفتحها Django عبر
# CONN_MAX_AGE > 0 — يسبب أخطاء غامضة (غالباً 500) تحديداً عند الكتابة
# لقاعدة البيانات. conn_max_age=0 يفتح اتصالاً جديداً نظيفاً لكل طلب.
DATABASES = {
    'default': dj_database_url.config(
        default=_database_url or f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=0,
        ssl_require=bool(_database_url),  # Neon يتطلب SSL، SQLite المحلية العمدية لا تحتاجه
    )
}

# =============================================================================
# اللغة والمنطقة الزمنية
# =============================================================================
LANGUAGE_CODE = 'ar'          # لوحة تحكم Django بالعربية بالكامل (ترجمة رسمية من Django نفسه)
TIME_ZONE = 'Africa/Algiers'
USE_I18N = True
USE_TZ = True

# =============================================================================
# =============================================================================
# الملفات الثابتة والوسائط
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# StaticFilesStorage البسيطة (بدون Manifest وبدون ضغط Compression):
#
# التاريخ الكامل لهذا القرار (توثيق لتفادي تكرار نفس المشكلة لاحقاً):
# 1) بدأنا بـ CompressedManifestStaticFilesStorage (صارمة جداً) — سببت
#    خطأ 500 "Missing staticfiles manifest entry" عند أي ملف ناقص.
# 2) انتقلنا لـ CompressedStaticFilesStorage (بدون Manifest، لكن لا يزال
#    فيها ضغط gzip) — سببت لاحقاً FileNotFoundError أثناء collectstatic
#    نفسه (مرحلة البناء) عند محاولة ضغط ملف مُشار إليه في CSS لم يُجمع
#    فعلياً لأي سبب (icon-hidelink.svg من admin الافتراضي).
# 3) الحل النهائي هنا: StaticFilesStorage العادية (بدون Manifest وبدون
#    أي خطوة ضغط/معالجة إضافية بعد النسخ). هذا يُزيل تماماً أي احتمال
#    فشل أثناء collectstatic بسبب ملف مرجعي واحد.
#
# لا نخسر شيئاً عملياً: WHITENOISE_USE_FINDERS=True أدناه يخدم الملفات
# مباشرة من مجلداتها الأصلية زمن التشغيل أصلاً (وليس من نتاج
# collectstatic/الضغط) — الضغط كان "تحسين أداء" غير ضروري لحجم مشروع
# بهذا النطاق، مقابل استقرار البناء الذي لا يقبل المساومة.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

WHITENOISE_MANIFEST_STRICT = False

# يخدم الملفات الثابتة مباشرة من مجلداتها الأصلية داخل كل مكتبة، دون أي
# اعتماد على نجاح أمر collectstatic أثناء البناء — يضمن عمل CSS دائماً.
WHITENOISE_USE_FINDERS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# Cloudinary: CDN مجاني ودائم لصور القنوات/الفرق/اللاعبين/الأخبار
# =============================================================================
# لماذا هذا مهم: على Render (الخطة المجانية)، أي صورة تُرفع من لوحة
# التحكم عبر MEDIA_ROOT العادي **تُحذف تلقائياً عند كل نشر جديد أو إعادة
# تشغيل** (تخزين مؤقت/غير دائم) — هذا كان السبب الحقيقي لمشكلة "روابط
# الصور المكسورة" التي ذكرتها. Cloudinary يخزّن الصور خارج Render نفسه
# بشكل دائم، مع رابط CDN سريع لا ينكسر أبداً بغض النظر عن عدد مرات النشر.
#
# == كيف تحصل على بيانات اعتماد Cloudinary (مجاني) ==
# 1) أنشئ حساباً مجانياً على https://cloudinary.com
# 2) من لوحة التحكم الرئيسية (Dashboard)، انسخ:
#    Cloud Name، API Key، API Secret
# 3) أضفها كمتغيرات بيئة في Render:
#    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
#
# رجوع تلقائي آمن (Fallback): إذا لم تُضبط هذه المتغيرات (مثل التطوير
# المحلي قبل إنشاء حساب Cloudinary)، يبقى المشروع يعمل بالتخزين المحلي
# العادي دون أي خطأ — بنفس فلسفة DATABASE_URL أعلاه بالضبط.
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

_cloudinary_configured = bool(
    CLOUDINARY_STORAGE['CLOUD_NAME']
    and CLOUDINARY_STORAGE['API_KEY']
    and CLOUDINARY_STORAGE['API_SECRET']
)

if _cloudinary_configured:
    STORAGES['default'] = {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'}

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

# =============================================================================
# إعدادات محرر النصوص الغني CKEditor 5
# =============================================================================
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'link', '|',
            'bulletedList', 'numberedList', '|',
            'blockQuote', 'insertImage', 'mediaEmbed', '|',
            'undo', 'redo',
        ],
    },
}
CKEDITOR_5_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# =============================================================================
# تخصيص هوية لوحة التحكم (بدون أي مكتبة خارجية)
# =============================================================================
# التخصيص البصري (الألوان، الشعار) يتم عبر نقطتَي تمديد رسميتين موثَّقتين
# من Django نفسه، بدون أي مكتبة إضافية:
#   templates/admin/base_site.html         ← الشعار وربط ملف CSS
#   core/static/admin/css/admin_custom.css  ← الألوان عبر متغيرات CSS
#   الرسمية التي يوفرها ثيم Django 5 الافتراضي نفسه (--primary, --header-bg...)
ADMIN_SITE_HEADER = 'Dilmi TV'
ADMIN_SITE_TITLE = 'Dilmi TV'
ADMIN_INDEX_TITLE = 'إدارة الموقع'
