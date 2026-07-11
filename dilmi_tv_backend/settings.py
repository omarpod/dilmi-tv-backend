"""
settings.py
-----------
مركز التحكم المحدث للمشروع - جاهز للنشر على Railway
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-REPLACE-THIS-KEY-BEFORE-PRODUCTION-1234567890'

# فعّلنا DEBUG مؤقتاً للتأكد من زوال الخطأ، يمكنك إعادته False لاحقاً
DEBUG = True

ALLOWED_HOSTS = [
    'web-production-d72c6.up.railway.app',
    '.railway.app',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'https://web-production-d72c6.up.railway.app',
    'https://*.railway.app',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = 'dilmi_tv_backend.urls'

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

WSGI_APPLICATION = 'dilmi_tv_backend.wsgi.application'

# === التعديل الجوهري لقاعدة البيانات ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'new_db.sqlite3', 
    }
}

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Algiers'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'underline', 'link', '|', 'bulletedList', 'numberedList', '|', 'blockQuote', 'insertImage', 'mediaEmbed', '|', 'undo', 'redo'],
    },
}
CKEDITOR_5_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

JAZZMIN_SETTINGS = {
    'site_title': 'Dilmi TV',
    'site_header': 'Dilmi TV',
    'site_brand': 'Dilmi TV',
    'site_logo': 'images/site_logo.png',
    'login_logo': 'images/site_logo.png',
    'login_logo_dark': 'images/site_logo.png',
    'site_icon': 'images/site_logo.png',
    'site_logo_classes': 'img-circle',
    'welcome_sign': 'مرحباً بك في لوحة إدارة Dilmi TV',
    'copyright': 'Dilmi TV',
    'search_model': ['core.Channel', 'core.Team', 'core.Match', 'core.News'],
    'topmenu_links': [{'name': 'عرض الموقع', 'url': '/', 'new_window': True}, {'model': 'auth.User'}],
    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.Group': 'fas fa-users',
        'auth.User': 'fas fa-user',
        'core.Channel': 'fas fa-tv',
        'core.Team': 'fas fa-shield-alt',
        'core.Player': 'fas fa-running',
        'core.Match': 'fas fa-futbol',
        'core.LineupEntry': 'fas fa-list-ol',
        'core.News': 'fas fa-newspaper',
        'core.AdSettings': 'fas fa-ad',
        'core.SiteSettings': 'fas fa-share-alt',
        'core.StaticPage': 'fas fa-file-alt',
        'core.Analytics': 'fas fa-chart-line',
        'core.NotificationSubscriber': 'fas fa-bell',
    },
    'default_icon_parents': 'fas fa-chevron-circle-left',
    'default_icon_children': 'fas fa-circle',
    'order_with_respect_to': [
        'core.Channel', 'core.Team', 'core.Player', 'core.Match',
        'core.LineupEntry', 'core.News',
        'core.AdSettings', 'core.SiteSettings', 'core.StaticPage',
        'core.Analytics', 'core.NotificationSubscriber',
        'auth',
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'changeform_format': 'horizontal_tabs',
    'related_modal_active': True,
    'show_ui_builder': False,
    'custom_css': 'admin/css/jazzmin_custom.css',
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False, 'footer_small_text': False, 'body_small_text': False, 'brand_small_text': False, 'brand_colour': False,
    'accent': 'accent-teal', 'navbar': 'navbar-dark navbar-teal', 'no_navbar_border': True, 'navbar_fixed': True,
    'layout_boxed': False, 'footer_fixed': False, 'sidebar_fixed': True, 'sidebar': 'sidebar-dark-teal',
    'sidebar_nav_small_text': False, 'sidebar_disable_expand': False, 'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False, 'sidebar_nav_legacy_style': False, 'sidebar_nav_flat_style': True,
    'theme': 'darkly', 'dark_mode_theme': 'darkly',
    'button_classes': {'primary': 'btn-outline-primary', 'secondary': 'btn-outline-secondary', 'info': 'btn-outline-info', 'warning': 'btn-outline-warning', 'danger': 'btn-outline-danger', 'success': 'btn-outline-success'},
    'actions_sticky_top': True,
}
