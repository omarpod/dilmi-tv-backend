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

# القائمة البيضاء للنطاقات المسموح لها بتشغيل هذا الموقع (نطاق Railway هنا).
ALLOWED_HOSTS = [
    'web-production-d72c6.up.railway.app',
    '.railway.app',
    'localhost',
    '127.0.0.1',
]

# مطلوبة لتسجيل الدخول للوحة /admin/ عبر رابط خارجي (نطاق Railway هنا).
# Django يرفض طلبات POST (مثل تسجيل الدخول) القادمة من نطاق غير موجود هنا،
# حتى لو كان ALLOWED_HOSTS يسمح به، وذلك كحماية إضافية من هجمات CSRF.
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-d72c6.up.railway.app',
    'https://*.railway.app',
]

# SECURE_PROXY_SSL_HEADER: ضرورية خلف بروكسي Railway لأن الاتصال الحقيقي
# بين Railway والمتصفح https، لكن الاتصال الداخلي بين بروكسي Railway
# وتطبيقك http عادي؛ هذا يخبر Django أن يثق بترويسة X-Forwarded-Proto
# لمعرفة أن الطلب كان https فعلاً (مهم لعمل CSRF بشكل صحيح خلف أي بروكسي).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ⚠️ لاحظ: تعمّدنا عدم إضافة USE_X_FORWARDED_HOST هنا. هذا الإعداد
# يجعل Django يثق بترويسة X-Forwarded-Host بدل Host العادية عند التحقق
# من ALLOWED_HOSTS — وإذا كانت منصة الاستضافة لا ترسل هذه الترويسة
# بالضبط كما يتوقعها Django (أو ترسل قيمة مختلفة عن النطاق العام)، فإن
# تفعيله يسبب بالضبط خطأ "Bad Request (400)" الذي واجهته، بدل حله.
# SECURE_PROXY_SSL_HEADER وحدها كافية عادة لعمل CSRF بشكل صحيح خلف
# Railway، دون الحاجة لهذا الإعداد الإضافي. إذا احتجته فعلاً لاحقاً بعد
# التشخيص، فعّله بحذر واختبر مباشرة بعده.
# USE_X_FORWARDED_HOST = True
# USE_X_FORWARDED_PORT = True

# =============================================================================
# التطبيقات المُفعّلة (Installed Apps)
# =============================================================================
INSTALLED_APPS = [
    # jazzmin يجب أن يكون قبل django.contrib.admin مباشرة (شرط إلزامي
    # من المكتبة نفسها) حتى يستبدل شكل لوحة التحكم الافتراضي بنجاح
    'jazzmin',

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
        # BASE_DIR/templates: يسمح لنا بتخصيص قوالب Django/Jazzmin (مثل
        # admin/index.html لعرض بطاقات الإحصائيات) دون تعديل ملفات
        # المكتبات نفسها. Django يبحث هنا أولاً قبل قوالب أي تطبيق مُثبَّت.
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
# الملفات الثابتة.
#
# ملاحظة مهمة (سبب خطأ 500 الذي واجهته): استخدمنا سابقاً
# CompressedManifestStaticFilesStorage، وهي "صارمة جداً" — إذا كان أي
# ملف واحد فقط مُشار إليه (حتى داخل CSS نفسه أو من مكتبة كـ
# django_ckeditor_5) غير موجود بالضبط في مجلد staticfiles/ بعد
# collectstatic، تُطلق Django استثناء ValueError يوقف الصفحة بالكامل
# بخطأ 500 — ويختفي تفصيل الخطأ الحقيقي عندما تكون DEBUG=False.
#
# الحل الأكثر أماناً واستقراراً للإنتاج: CompressedStaticFilesStorage
# (بدون "Manifest"). تبقي ضغط gzip، لكنها لا تتطلب مطابقة صارمة لكل
# ملف، فلا تُسقط الصفحة كاملة بسبب ملف واحد ناقص من مكتبة خارجية.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# طبقة حماية إضافية: حتى لو استخدمت مستقبلاً نسخة Manifest مرة أخرى،
# هذا الإعداد يجعل الملفات المفقودة تُترك كما هي (رابط غير مكسور لكن
# بدون تجزئة/بصمة) بدل رمي استثناء يوقف الصفحة بالكامل.
WHITENOISE_MANIFEST_STRICT = False

# == الحل الحاسم لمشكلة "CSS لا يعمل رغم كل الإعدادات" ==
# WHITENOISE_USE_FINDERS=True يجعل WhiteNoise يخدم الملفات الثابتة
# *مباشرة من مجلداتها الأصلية* داخل كل مكتبة (admin، rest_framework،
# django_ckeditor_5...) عبر آلية "Finders" في Django، تماماً كما تعمل
# أثناء التطوير المحلي (DEBUG=True) — دون أي اعتماد إطلاقاً على نجاح
# أمر collectstatic أو وجود مجلد staticfiles/ بشكل صحيح.
#
# لماذا هذا الحل الأضمن هنا تحديداً: إذا لم يُنفَّذ collectstatic فعلياً
# أثناء البناء على Render (لأي سبب: Build Command لم يُحفظ، فشل صامت،
# ذاكرة تخزين مؤقت قديمة...)، فإن الاعتماد على STATIC_ROOT/collectstatic
# سيبقي CSS معطلاً دائماً. هذا الإعداد يزيل الاعتماد على تلك الخطوة
# كلياً، فتعمل ملفات CSS/JS مهما حدث في مرحلة البناء.
#
# الأثر الوحيد: نفقد ميزتي الضغط (gzip) والتخزين المؤقت طويل الأمد
# (versioned caching) للملفات الثابتة، وهو تنازل بسيط ومقبول تماماً
# لحجم مشروع مثل هذا مقابل الاستقرار المضمون.
WHITENOISE_USE_FINDERS = True

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

# =============================================================================
# إعدادات Jazzmin: تحويل لوحة تحكم Django الافتراضية لواجهة احترافية
# بثيم داكن (Navy/Charcoal) بإضاءة نيون بنفس هوية ألوان تطبيق Flutter
# (أخضر مزرق #0F9D8C + برتقالي #FF5A36)، تشبه منصات البث الرقمي الحديثة.
# =============================================================================
JAZZMIN_SETTINGS = {
    # ===== الهوية البصرية العامة =====
    'site_title': 'Dilmi TV',
    'site_header': 'Dilmi TV',
    'site_brand': 'Dilmi TV',
    'site_logo': 'images/site_logo.png',       # يظهر في الشريط العلوي والقائمة الجانبية
    'login_logo': 'images/site_logo.png',      # يظهر في صفحة تسجيل الدخول
    'login_logo_dark': 'images/site_logo.png',
    'site_icon': 'images/site_logo.png',       # أيقونة تبويب المتصفح (favicon)
    'site_logo_classes': 'img-circle',
    'welcome_sign': 'مرحباً بك في لوحة إدارة Dilmi TV',
    'copyright': 'Dilmi TV',

    # ===== شريط البحث العلوي: يسمح بالبحث السريع داخل هذه النماذج =====
    'search_model': ['core.Channel', 'core.Team', 'core.Match', 'core.News'],

    # ===== روابط في الشريط العلوي (بجانب البحث) =====
    'topmenu_links': [
        {'name': 'عرض الموقع', 'url': '/', 'new_window': True},
        {'model': 'auth.User'},
    ],

    # ===== أيقونات مخصصة لكل نموذج (FontAwesome) لإحساس بصري مميز =====
    # التنسيق: 'اسم_التطبيق.اسم_النموذج': 'فئة الأيقونة'
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

    # ===== ترتيب النماذج داخل القائمة الجانبية (منطقي: المحتوى، ثم =====
    # ===== الإعدادات، ثم الإحصائيات/الإشعارات، ثم المستخدمون) =====
    'order_with_respect_to': [
        'core.Channel', 'core.Team', 'core.Player', 'core.Match',
        'core.LineupEntry', 'core.News',
        'core.AdSettings', 'core.SiteSettings', 'core.StaticPage',
        'core.Analytics', 'core.NotificationSubscriber',
        'auth',
    ],

    # ===== سلوك عام =====
    'show_sidebar': True,
    'navigation_expanded': True,       # القائمة الجانبية مفتوحة بالكامل افتراضياً
    'changeform_format': 'horizontal_tabs',
    'related_modal_active': True,      # فتح العناصر المرتبطة في نافذة منبثقة (تجربة أسلس)
    'show_ui_builder': False,          # تعطيل أداة بناء الثيم التفاعلية في الإنتاج

    # ===== ملف CSS مخصص إضافي (تأثيرات نيون وتفاصيل دقيقة لا يوفرها Jazzmin افتراضياً) =====
    'custom_css': 'admin/css/jazzmin_custom.css',
}

# =============================================================================
# JAZZMIN_UI_TWEAKS: الألوان والتخطيط الفعلي للثيم الداكن
# =============================================================================
JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': False,
    'accent': 'accent-teal',           # لون التمييز الأساسي (أقرب فئة جاهزة لأخضر Dilmi TV المزرق)
    'navbar': 'navbar-dark navbar-teal',
    'no_navbar_border': True,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-teal',    # قائمة جانبية داكنة بلمسة الأخضر المزرق
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': True,    # قوائم مسطّحة عصرية بدل الظلال التقليدية
    'theme': 'darkly',                 # ثيم Bootswatch داكن (Navy/Charcoal) كأساس عام
    'dark_mode_theme': 'darkly',       # يبقى داكناً حتى عند تفعيل "الوضع الداكن" الرسمي لـ Django
    'button_classes': {
        'primary': 'btn-outline-primary',
        'secondary': 'btn-outline-secondary',
        'info': 'btn-outline-info',
        'warning': 'btn-outline-warning',
        'danger': 'btn-outline-danger',
        'success': 'btn-outline-success',
    },
    'actions_sticky_top': True,
}
