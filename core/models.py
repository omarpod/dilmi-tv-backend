"""
models.py
---------
نسخة محدثة: تم تحصين دالة __str__ لمنع انهيار لوحة التحكم عند وجود بيانات ناقصة.
"""
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class Channel(models.Model):
    name = models.CharField('اسم القناة', max_length=100)
    logo = models.ImageField('شعار القناة', upload_to='channels/logos/', blank=True, null=True)
    stream_url = models.URLField('رابط البث المباشر', max_length=500)
    category = models.CharField(
        'الفئة', max_length=50,
        choices=[('sports', 'رياضة'), ('news', 'أخبار'), ('general', 'عام')],
        default='sports',
    )
    is_active = models.BooleanField('مفعّلة؟', default=True)
    order = models.PositiveIntegerField('ترتيب الظهور', default=0)
    created_at = models.DateTimeField('تاريخ الإضافة', auto_now_add=True)

    class Meta:
        verbose_name = 'قناة'
        verbose_name_plural = 'القنوات'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class League(models.Model):
    name = models.CharField('اسم البطولة', max_length=150)
    logo = models.ImageField('شعار البطولة', upload_to='leagues/logos/', blank=True, null=True)
    country = models.CharField('الدولة', max_length=100, blank=True)
    external_id = models.CharField(
        'المعرّف الخارجي (API-Football)', max_length=50, blank=True, null=True, unique=True,
    )

    class Meta:
        verbose_name = 'بطولة'
        verbose_name_plural = 'البطولات'
        ordering = ['name']

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField('اسم الفريق', max_length=100)
    logo = models.ImageField('شعار الفريق', upload_to='teams/logos/', blank=True, null=True)
    country = models.CharField('الدولة', max_length=100, blank=True)
    external_id = models.CharField(
        'المعرّف الخارجي (API-Football)', max_length=50, blank=True, null=True, unique=True,
    )

    class Meta:
        verbose_name = 'فريق'
        verbose_name_plural = 'الفرق'
        ordering = ['name']

    def __str__(self):
        return self.name


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players', verbose_name='الفريق')
    name = models.CharField('اسم اللاعب', max_length=100)
    photo = models.ImageField('صورة اللاعب', upload_to='players/photos/', blank=True, null=True)
    shirt_number = models.PositiveIntegerField('رقم القميص', default=0)
    position = models.CharField(
        'المركز', max_length=20,
        choices=[('GK', 'حارس مرمى'), ('DF', 'مدافع'), ('MF', 'وسط'), ('FW', 'مهاجم')],
        default='MF',
    )
    external_id = models.CharField(
        'المعرّف الخارجي (API-Football)', max_length=50, blank=True, null=True, unique=True,
    )

    class Meta:
        verbose_name = 'لاعب'
        verbose_name_plural = 'اللاعبون'
        ordering = ['team', 'shirt_number']

    def __str__(self):
        return f'{self.name} ({self.team.name if self.team else "لا فريق"})'


class Match(models.Model):
    STATUS_CHOICES = [('upcoming', 'لم تبدأ بعد'), ('live', 'مباشر الآن'), ('finished', 'انتهت')]
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches', verbose_name='الفريق المضيف')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches', verbose_name='الفريق الضيف')
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches', verbose_name='قناة البث')
    league = models.ForeignKey(League, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches', verbose_name='البطولة')
    competition = models.CharField('البطولة/الدوري (نص احتياطي)', max_length=150, blank=True)
    match_datetime = models.DateTimeField('موعد المباراة')
    status = models.CharField('حالة المباراة', max_length=10, choices=STATUS_CHOICES, default='upcoming')
    home_score = models.PositiveIntegerField('أهداف الفريق المضيف', default=0)
    away_score = models.PositiveIntegerField('أهداف الفريق الضيف', default=0)
    elapsed_minutes = models.PositiveIntegerField('الدقيقة الحالية', default=0, blank=True)
    external_id = models.CharField('المعرّف الخارجي (API-Football)', max_length=50, blank=True, null=True, unique=True)

    class Meta:
        verbose_name = 'مباراة'
        verbose_name_plural = 'المباريات'
        ordering = ['match_datetime']

    @property
    def competition_display(self):
        return self.league.name if self.league else self.competition

    def __str__(self):
        # تعديل دفاعي: تحقق من وجود الفرق قبل الوصول لخاصية الاسم
        home = self.home_team.name if self.home_team else "فريق غير معروف"
        away = self.away_team.name if self.away_team else "فريق غير معروف"
        return f'{home} vs {away} - {self.match_datetime.strftime("%Y-%m-%d %H:%M") if self.match_datetime else "بدون موعد"}'


class MatchEvent(models.Model):
    EVENT_TYPE_CHOICES = [('goal', 'هدف'), ('yellow_card', 'بطاقة صفراء'), ('red_card', 'بطاقة حمراء'), ('substitution', 'تبديل')]
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events', verbose_name='المباراة')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name='الفريق')
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='اللاعب')
    minute = models.PositiveIntegerField('الدقيقة')
    event_type = models.CharField('نوع الحدث', max_length=20, choices=EVENT_TYPE_CHOICES)
    description = models.CharField('تفاصيل إضافية', max_length=200, blank=True)
    external_id = models.CharField('المعرّف الخارجي', max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'حدث مباراة'
        verbose_name_plural = 'أحداث المباريات'
        ordering = ['match', 'minute']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.player or self.team} ({self.minute}')"

class LineupEntry(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='lineup', verbose_name='المباراة')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='اللاعب')
    is_starting = models.BooleanField('أساسي؟', default=True)

    class Meta:
        verbose_name = 'عنصر تشكيلة'
        verbose_name_plural = 'التشكيلات'
        unique_together = ('match', 'player')

    def __str__(self):
        return f'{self.player.name if self.player else "لاعب"} - {self.match}'

class News(models.Model):
    title = models.CharField('العنوان', max_length=200)
    content = models.TextField('المحتوى')
    image = models.ImageField('صورة الخبر', upload_to='news/images/', blank=True, null=True)
    related_match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, blank=True, related_name='news', verbose_name='مرتبط بمباراة')
    published_at = models.DateTimeField('تاريخ النشر', auto_now_add=True)
    is_published = models.BooleanField('منشور؟', default=True)

    class Meta:
        verbose_name = 'خبر'
        verbose_name_plural = 'الأخبار'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

class AdSettings(models.Model):
    banner_ad_unit_id = models.CharField('معرّف إعلان البانر', max_length=100, blank=True)
    interstitial_ad_unit_id = models.CharField('معرّف الإعلان البيني', max_length=100, blank=True)
    banner_enabled = models.BooleanField('تفعيل إعلانات البانر', default=True)
    interstitial_enabled = models.BooleanField('تفعيل الإعلانات البينية', default=True)
    updated_at = models.DateTimeField('آخر تحديث', auto_now=True)

    class Meta:
        verbose_name = 'إعدادات الإعلانات'
        verbose_name_plural = 'إعدادات الإعلانات (AdMob)'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'إعدادات AdMob'

class Analytics(models.Model):
    ip_address = models.GenericIPAddressField('عنوان IP', null=True, blank=True)
    device = models.CharField('الجهاز', max_length=150, blank=True)
    screen = models.CharField('الشاشة/الحدث', max_length=100, blank=True)
    timestamp = models.DateTimeField('التوقيت', auto_now_add=True)

    class Meta:
        verbose_name = 'زيارة'
        verbose_name_plural = 'الإحصائيات (الزوار)'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.device or "جهاز غير معروف"} - {self.timestamp.strftime("%Y-%m-%d %H:%M")}'

class SiteSettings(models.Model):
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
    fcm_token = models.CharField('رمز الجهاز (FCM Token)', max_length=255, unique=True)
    device_platform = models.CharField('نظام الجهاز', max_length=20, choices=[('android', 'أندرويد'), ('ios', 'آيفون')], default='android')
    is_active = models.BooleanField('نشِط؟', default=True)
    subscribed_at = models.DateTimeField('تاريخ الاشتراك', auto_now_add=True)

    class Meta:
        verbose_name = 'مشترك إشعارات'
        verbose_name_plural = 'مشتركو الإشعارات (FCM)'
        ordering = ['-subscribed_at']

    def __str__(self):
        return f'{self.device_platform} - {self.fcm_token[:20]}...'

class StaticPage(models.Model):
    PAGE_CHOICES = [('privacy_policy', 'سياسة الخصوصية'), ('about_us', 'من نحن')]
    slug = models.CharField('الصفحة', max_length=30, choices=PAGE_CHOICES, unique=True)
    title = models.CharField('العنوان المعروض', max_length=150)
    content = CKEditor5Field('المحتوى', config_name='default')
    updated_at = models.DateTimeField('آخر تحديث', auto_now=True)

    class Meta:
        verbose_name = 'صفحة ثابتة'
        verbose_name_plural = 'الصفحات الثابتة'

    def __str__(self):
        return self.title