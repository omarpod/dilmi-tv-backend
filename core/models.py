"""
models.py
---------
هذا الملف هو "تصميم قاعدة البيانات". كل class هنا يمثل جدولاً (Table) في
قاعدة بيانات SQLite. Django يقرأ هذا الملف ويُنشئ الجداول تلقائياً عند تنفيذ:
    python manage.py makemigrations
    python manage.py migrate

كل حقل (field) هنا = عمود في الجدول.
"""
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class Channel(models.Model):
    """
    جدول القنوات: كل قناة رياضية ستُعرض في التطبيق (رابط البث + معلوماتها).
    """
    name = models.CharField('اسم القناة', max_length=100)
    logo = models.ImageField('شعار القناة', upload_to='channels/logos/', blank=True, null=True)

    # رابط البث المباشر (m3u8 أو أي رابط ستريم يفهمه مشغل الفيديو في التطبيق)
    stream_url = models.URLField('رابط البث المباشر', max_length=500)

    category = models.CharField(
        'الفئة', max_length=50,
        choices=[('sports', 'رياضة'), ('news', 'أخبار'), ('general', 'عام')],
        default='sports',
    )

    # يسمح للمدير بإخفاء قناة مؤقتاً (مثلاً إذا توقف الرابط عن العمل)
    # دون حذفها نهائياً من قاعدة البيانات
    is_active = models.BooleanField('مفعّلة؟', default=True)

    order = models.PositiveIntegerField('ترتيب الظهور', default=0)

    created_at = models.DateTimeField('تاريخ الإضافة', auto_now_add=True)

    class Meta:
        verbose_name = 'قناة'
        verbose_name_plural = 'القنوات'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Team(models.Model):
    """جدول الفرق الرياضية."""
    name = models.CharField('اسم الفريق', max_length=100)
    logo = models.ImageField('شعار الفريق', upload_to='teams/logos/', blank=True, null=True)
    country = models.CharField('الدولة', max_length=100, blank=True)

    class Meta:
        verbose_name = 'فريق'
        verbose_name_plural = 'الفرق'
        ordering = ['name']

    def __str__(self):
        return self.name


class Player(models.Model):
    """
    جدول اللاعبين، كل لاعب مرتبط بفريق واحد.
    on_delete=CASCADE يعني: إذا حُذف الفريق، تُحذف لاعبوه تلقائياً معه.
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players', verbose_name='الفريق')
    name = models.CharField('اسم اللاعب', max_length=100)
    shirt_number = models.PositiveIntegerField('رقم القميص', default=0)
    position = models.CharField(
        'المركز', max_length=20,
        choices=[
            ('GK', 'حارس مرمى'), ('DF', 'مدافع'),
            ('MF', 'وسط'), ('FW', 'مهاجم'),
        ],
        default='MF',
    )

    class Meta:
        verbose_name = 'لاعب'
        verbose_name_plural = 'اللاعبون'
        ordering = ['team', 'shirt_number']

    def __str__(self):
        return f'{self.name} ({self.team.name})'


class Match(models.Model):
    """جدول المباريات: يربط بين فريقين وقناة البث، مع الحالة والنتيجة."""

    STATUS_CHOICES = [
        ('upcoming', 'لم تبدأ بعد'),
        ('live', 'مباشر الآن'),
        ('finished', 'انتهت'),
    ]

    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches', verbose_name='الفريق المضيف')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches', verbose_name='الفريق الضيف')

    # ربط المباراة بالقناة التي ستبث عليها (اختياري: قد لا تُحدد القناة بعد)
    channel = models.ForeignKey(
        Channel, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matches', verbose_name='قناة البث',
    )

    competition = models.CharField('البطولة/الدوري', max_length=150, blank=True)
    match_datetime = models.DateTimeField('موعد المباراة')

    status = models.CharField('حالة المباراة', max_length=10, choices=STATUS_CHOICES, default='upcoming')

    home_score = models.PositiveIntegerField('أهداف الفريق المضيف', default=0)
    away_score = models.PositiveIntegerField('أهداف الفريق الضيف', default=0)

    class Meta:
        verbose_name = 'مباراة'
        verbose_name_plural = 'المباريات'
        ordering = ['match_datetime']

    def __str__(self):
        return f'{self.home_team} vs {self.away_team} - {self.match_datetime:%Y-%m-%d %H:%M}'


class LineupEntry(models.Model):
    """
    جدول التشكيلة: يحدد أي لاعب يلعب في أي مباراة، ولأي فريق،
    وهل هو أساسي أم احتياطي. هذا جدول "وسيط" يربط Match و Player معاً.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='lineup', verbose_name='المباراة')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='اللاعب')
    is_starting = models.BooleanField('أساسي؟', default=True)  # False = احتياطي

    class Meta:
        verbose_name = 'عنصر تشكيلة'
        verbose_name_plural = 'التشكيلات'
        # يمنع تكرار نفس اللاعب مرتين في نفس المباراة
        unique_together = ('match', 'player')

    def __str__(self):
        return f'{self.player.name} - {self.match}'


class News(models.Model):
    """جدول الأخبار: أخبار عامة أو مرتبطة بمباراة معينة."""
    title = models.CharField('العنوان', max_length=200)
    content = models.TextField('المحتوى')
    image = models.ImageField('صورة الخبر', upload_to='news/images/', blank=True, null=True)

    # اختياري: ربط الخبر بمباراة معينة (مثل "ملخص مباراة الأمس")
    related_match = models.ForeignKey(
        Match, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='news', verbose_name='مرتبط بمباراة',
    )

    published_at = models.DateTimeField('تاريخ النشر', auto_now_add=True)
    is_published = models.BooleanField('منشور؟', default=True)

    class Meta:
        verbose_name = 'خبر'
        verbose_name_plural = 'الأخبار'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class AdSettings(models.Model):
    """
    إعدادات إعلانات AdMob. هذا الجدول مصمم ليحتوي على "سجل واحد فقط"
    (Singleton) لأن التطبيق يحتاج إعدادات إعلانات واحدة فقط في كل مرة.
    """
    banner_ad_unit_id = models.CharField('معرّف إعلان البانر (Banner)', max_length=100, blank=True)
    interstitial_ad_unit_id = models.CharField('معرّف الإعلان البيني (Interstitial)', max_length=100, blank=True)

    banner_enabled = models.BooleanField('تفعيل إعلانات البانر', default=True)
    interstitial_enabled = models.BooleanField('تفعيل الإعلانات البينية', default=True)

    updated_at = models.DateTimeField('آخر تحديث', auto_now=True)

    class Meta:
        verbose_name = 'إعدادات الإعلانات'
        verbose_name_plural = 'إعدادات الإعلانات (AdMob)'

    def save(self, *args, **kwargs):
        # يجبر النموذج على أن يكون له سجل واحد فقط (id=1 دائماً)
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'إعدادات AdMob'


# =============================================================================
# النماذج الجديدة: الإحصائيات، الإعدادات العامة، مشتركو الإشعارات، الصفحات الثابتة
# =============================================================================

class Analytics(models.Model):
    """
    سجل زيارات بسيط: كل مرة يفتح فيها أحد التطبيق (أو يزور شاشة معينة)،
    نسجّل سطراً هنا. هذا يبني "نظام إحصائيات دقيق للزوار" كما طُلب،
    دون تعقيد إضافة مكتبات تحليلات خارجية.

    ملاحظة تصميم: هذا الجدول يكبر بسرعة مع الاستخدام (سطر لكل زيارة)،
    لذا يُفضّل لاحقاً أرشفة أو حذف السجلات القديمة دورياً إذا كبر
    عدد المستخدمين كثيراً (خارج نطاق هذا التحديث الحالي).
    """
    ip_address = models.GenericIPAddressField('عنوان IP', null=True, blank=True)

    device = models.CharField(
        'الجهاز', max_length=150, blank=True,
        help_text='مثال: Android 14 - Samsung SM-G991B، يرسله التطبيق تلقائياً',
    )

    # أي شاشة/حدث زاره المستخدم، مفيد لمعرفة أكثر الأقسام استخداماً
    screen = models.CharField(
        'الشاشة/الحدث', max_length=100, blank=True,
        help_text='مثال: home, channel_open, news_detail',
    )

    timestamp = models.DateTimeField('التوقيت', auto_now_add=True)

    class Meta:
        verbose_name = 'زيارة'
        verbose_name_plural = 'الإحصائيات (الزوار)'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.device or "جهاز غير معروف"} - {self.timestamp:%Y-%m-%d %H:%M}'


class SiteSettings(models.Model):
    """
    الإعدادات العامة للموقع/التطبيق: روابط التواصل الاجتماعي والبريد.
    مثل AdSettings، هذا الجدول "سجل واحد فقط" (Singleton) لأن التطبيق
    يحتاج نسخة واحدة فقط من هذه الإعدادات في كل وقت.

    ملاحظة: سمّيناه SiteSettings (وليس Settings فقط) عمداً لتفادي أي
    تعارض أو التباس مع ملف dilmi_tv_backend/settings.py نفسه.
    """
    facebook_url = models.URLField('رابط فيسبوك', blank=True)
    instagram_url = models.URLField('رابط انستغرام', blank=True)
    telegram_url = models.URLField('رابط تيليجرام', blank=True)
    contact_email = models.EmailField('البريد الإلكتروني للتواصل', blank=True)

    updated_at = models.DateTimeField('آخر تحديث', auto_now=True)

    class Meta:
        verbose_name = 'الإعدادات العامة'
        verbose_name_plural = 'الإعدادات العامة (تواصل اجتماعي)'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'الإعدادات العامة'


class NotificationSubscriber(models.Model):
    """
    يخزّن رمز جهاز Firebase Cloud Messaging (FCM Token) لكل مستخدم ثبّت
    التطبيق وسمح بالإشعارات، لنتمكن لاحقاً من إرسال إشعارات Push حقيقية
    له حتى لو كان التطبيق مغلقاً تماماً (خلافاً للإشعارات المحلية السابقة
    التي تعمل فقط أثناء تشغيل التطبيق).
    """
    fcm_token = models.CharField(
        'رمز الجهاز (FCM Token)', max_length=255, unique=True,
        help_text='يُرسله تطبيق Flutter تلقائياً عند أول تشغيل',
    )

    device_platform = models.CharField(
        'نظام الجهاز', max_length=20,
        choices=[('android', 'أندرويد'), ('ios', 'آيفون')],
        default='android',
    )

    is_active = models.BooleanField(
        'نشِط؟', default=True,
        help_text='يُعطّل تلقائياً إذا رفض الرمز عند محاولة الإرسال (جهاز أُلغي تثبيت التطبيق منه)',
    )

    subscribed_at = models.DateTimeField('تاريخ الاشتراك', auto_now_add=True)

    class Meta:
        verbose_name = 'مشترك إشعارات'
        verbose_name_plural = 'مشتركو الإشعارات (FCM)'
        ordering = ['-subscribed_at']

    def __str__(self):
        return f'{self.device_platform} - {self.fcm_token[:20]}...'


class StaticPage(models.Model):
    """
    صفحات ثابتة مثل "سياسة الخصوصية" و "من نحن". نستخدم PAGE_CHOICES
    بدل السماح بإنشاء صفحات بأي مفتاح حر، حتى يعرف تطبيق Flutter دائماً
    بالضبط أي صفحة يطلب عبر مفتاح ثابت متفق عليه مسبقاً (slug).

    مطلب تقني: حقل content يدعم HTML منسّق (وليس نصاً عادياً فقط)، عبر
    CKEditor5Field من مكتبة django-ckeditor-5، لتتمكن من التنسيق (عناوين،
    قوائم، روابط، صور...) مباشرة من لوحة التحكم دون كتابة وسوم HTML يدوياً.
    """
    PAGE_CHOICES = [
        ('privacy_policy', 'سياسة الخصوصية'),
        ('about_us', 'من نحن'),
    ]

    slug = models.CharField(
        'الصفحة', max_length=30, choices=PAGE_CHOICES, unique=True,
    )
    title = models.CharField('العنوان المعروض', max_length=150)

    # CKEditor5Field يخزّن HTML كامل في قاعدة البيانات (نص عادي في العمود،
    # لكن لوحة التحكم تعرضه بمحرر نصوص غني بدل textarea عادي)
    content = CKEditor5Field('المحتوى', config_name='default')

    updated_at = models.DateTimeField('آخر تحديث', auto_now=True)

    class Meta:
        verbose_name = 'صفحة ثابتة'
        verbose_name_plural = 'الصفحات الثابتة'

    def __str__(self):
        return self.title
