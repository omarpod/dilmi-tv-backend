"""
settings.py
-----------
هذا هو "مركز التحكم" في المشروع كله. كل الإعدادات العامة (قاعدة البيانات،
التطبيقات المُفعّلة، الأمان، اللغة...) موجودة هنا.
"""

from pathlib import Path

# BASE_DIR: المسار الجذري للمشروع (المجلد الذي يحتوي على manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# إعدادات الأمان
# =============================================================================

# مفتاح سري يستخدمه Django داخلياً للتشفير. 
# تحذير: قبل رفع المشروع للإنتاج الحقيقي، غيّر هذا المفتاح واجعله سرياً
# (لا تضعه في GitHub علناً). يمكن قراءته من متغير بيئة لاحقاً.
SECRET_KEY = 'django-insecure-REPLACE-THIS-KEY-BEFORE-PRODUCTION-1234567890'

# DEBUG = True مفيد فقط أثناء التطوير (يعرض لك تفاصيل الأخطاء).
# يجب أن تجعله False عند النشر الفعلي على الإنترنت.
DEBUG = False

# القائمة البيضاء للنطاقات/العناوين المسموح لها بتشغيل هذا الموقع.
# أثناء التطوير المحلي نتركها فارغة أو نضع '*' لتسهيل التجربة.
ALLOWED_HOSTS = ['*']

# مطلوبة فقط إذا أردت تسجيل الدخول للوحة التحكم /admin/ عبر رابط خارجي
# (مثل رابط نفق Serveo/ngrok) وليس فقط عبر 127.0.0.1 محلياً.
# Django يرفض طلبات POST (مثل تسجيل الدخول) القادمة من نطاق غير موجود هنا،
# حتى لو كان ALLOWED_HOSTS يسمح به، وذلك كحماية إضافية من هجمات CSRF.
# إذا واجهت خطأ "CSRF verification failed" عند الدخول للوحة التحكم عبر
# رابط Serveo، أضف رابطك هنا (استبدل الرابط التالي برابطك الفعلي):
CSRF_TRUSTED_ORIGINS = [
    'https://*.serveousercontent.com',
]

# =============================================================================
# التطبيقات المُفعّلة (Installed Apps)
# =============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',        # لوحة تحكم Django الجاهزة
    'django.contrib.auth',         # نظام المستخدمين وتسجيل الدخول
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # لخدمة ملفات CSS/JS/الصور

    'rest_framework',              # مكتبة بناء الـ API
    'corsheaders',                 # للسماح لتطبيق الأندرويد بالاتصال بالـ API
    'django_ckeditor_5',           # محرر نصوص غني (HTML) لصفحات "من نحن" و"سياسة الخصوصية"

    'core',                        # تطبيقنا الخاص (سننشئه بالخطوات القادمة)
]

# =============================================================================
# الوسائط (Middleware): طبقات تعالج كل طلب قبل وبعد وصوله للـ views
# =============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # يجب أن تكون في الأعلى قدر الإمكان
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise: يجب أن تكون مباشرة بعد SecurityMiddleware وقبل أي شيء
    # آخر، لتخدم ملفات CSS/JS الثابتة (بما فيها تنسيق لوحة /admin نفسها)
    # مباشرة من عملية Gunicorn دون الحاجة لخادم ويب منفصل
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# أثناء التطوير: نسمح لأي مصدر بالاتصال بالـ API (تطبيق الأندرويد على المحاكي مثلاً).
# عند النشر الحقيقي، استبدل هذا بقائمة محددة من النطاقات المسموحة.
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
# قاعدة البيانات: SQLite (ملف واحد بسيط، مناسب جداً للبداية والتعلم)
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # سيُنشأ هذا الملف تلقائياً عند migrate
    }
}

# =============================================================================
# اللغة والمنطقة الزمنية
# =============================================================================
LANGUAGE_CODE = 'ar'          # لجعل لوحة تحكم Django الجاهزة تظهر بالعربية
TIME_ZONE = 'Africa/Algiers'  # يمكنك تغييرها حسب منطقتك
USE_I18N = True
USE_TZ = True

# =============================================================================
# الملفات الثابتة والوسائط (صور القنوات، شعارات الفرق...)
# =============================================================================
STATIC_URL = 'static/'

# STATIC_ROOT: المجلد الذي يجمع فيه أمر collectstatic كل ملفات CSS/JS من
# كل تطبيق (admin، rest_framework، ckeditor5...) في مكان واحد ليخدمها
# WhiteNoise منه في الإنتاج. هذا الأمر يُنفَّذ في مرحلة "Build" فقط على
# Render (راجع إعدادات Render في ملف RENDER_DEPLOY_FIX.md)، وليس أثناء
# التشغيل الفعلي، لذلك لا يتأثر بقيود الكتابة وقت التشغيل على الخطة المجانية.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# STORAGES: الطريقة الحديثة (منذ Django 4.2+) لتحديد كيفية تخزين/خدمة
# الملفات الثابتة. CompressedManifestStaticFilesStorage من WhiteNoise
# تضغط الملفات (gzip) وتضيف "بصمة" لاسم كل ملف لدعم التخزين المؤقت
# (caching) الآمن في متصفح الزائر لفترة طويلة دون مشاكل عند التحديث.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'   # هنا ستُحفظ الصور التي يرفعها المدير

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# إعدادات Django REST Framework
# =============================================================================
REST_FRAMEWORK = {
    # بشكل افتراضي، أي شخص يمكنه "القراءة فقط" من الـ API (GET)
    # بينما الكتابة (إضافة/تعديل) تتم فقط عبر لوحة تحكم /admin
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# =============================================================================
# إعدادات محرر النصوص الغني CKEditor 5 (لحقل content في StaticPage)
# =============================================================================
# customColorPalette فارغة تعني استخدام الألوان الافتراضية للمحرر.
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
# مسار رفع الصور المُدرجة داخل محتوى المحرر نفسه (مختلف عن MEDIA_ROOT العام)
CKEDITOR_5_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
