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
DEBUG = True

# القائمة البيضاء للنطاقات/العناوين المسموح لها بتشغيل هذا الموقع.
# أثناء التطوير المحلي نتركها فارغة أو نضع '*' لتسهيل التجربة.
ALLOWED_HOSTS = ['*']
# أضف هذا السطر بالضبط بعد ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = [
    'https://d5c7a57daf9b5559-41-200-3-198.serveousercontent.com',
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

    'core',                        # تطبيقنا الخاص (سننشئه بالخطوات القادمة)
]

# =============================================================================
# الوسائط (Middleware): طبقات تعالج كل طلب قبل وبعد وصوله للـ views
# =============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # يجب أن تكون في الأعلى قدر الإمكان
    'django.middleware.security.SecurityMiddleware',
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
