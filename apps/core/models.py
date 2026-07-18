"""
apps/core/models.py
---------------------
النماذج الأساسية الثلاثة: Channel, Match, News — كل منها بمعرّف UUID
بدل الترقيم التسلسلي العادي (1, 2, 3...).

== لماذا UUID تحديداً (أمان) ==
مع الترقيم التسلسلي، يمكن لأي شخص تخمين وجود سجلات أخرى بسهولة (إذا
رأى /api/matches/7/، يعرف فوراً أن 1-6 موجودة، ويمكنه "تعداد" كل
السجلات بالتخمين — Insecure Direct Object Reference). مع UUID
(مثال: 3fa85f64-5717-4562-b3fc-2c963f66afa6)، يستحيل تخمين أي معرّف
آخر عملياً، حتى لو كان الرابط عاماً.
"""
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    كلاس أساس مجرَّد (Abstract Base Class) — يضيف created_at وupdated_at
    تلقائياً لأي نموذج يرثه، بدل تكرار نفس السطرين في كل نموذج على حدة.
    """
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ آخر تحديث', auto_now=True)

    class Meta:
        abstract = True  # لا يُنشئ جدولاً خاصاً به، فقط حقول تُورَّث


class Channel(TimeStampedModel):
    """قناة بث مباشر (رياضية، إخبارية...)."""

    class Category(models.TextChoices):
        SPORTS = 'sports', 'رياضة'
        NEWS = 'news', 'أخبار'
        GENERAL = 'general', 'عام'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField('اسم القناة', max_length=100)
    logo = models.ImageField('شعار القناة', upload_to='channels/logos/', blank=True, null=True)
    # رابط البث الوحيد القديم (stream_url) انتقل إلى apps.streaming.StreamSource
    # — كل قناة تدعم الآن عدة روابط مرتّبة بالأولوية (راجع related_name='sources')
    category = models.CharField('التصنيف', max_length=20, choices=Category.choices, default=Category.SPORTS)

    is_active = models.BooleanField('نشِطة؟', default=True)
    order = models.PositiveIntegerField('ترتيب الظهور', default=0)

    class Meta:
        verbose_name = 'قناة'
        verbose_name_plural = 'القنوات'
        ordering = ['order', 'name']
        indexes = [
            # فهرس على (is_active, category) معاً — الاستعلام الأشيع في
            # التطبيق هو "أعطني القنوات النشِطة من تصنيف معيّن"، فهذا
            # الفهرس المُركَّب يُسرّعه مباشرة بدل فهرسة كل عمود منفصلاً
            models.Index(fields=['is_active', 'category']),
        ]

    def __str__(self):
        return self.name


class Match(TimeStampedModel):
    """مباراة رياضية — بيانات الفريقين مُضمَّنة كحقول نصية مباشرة (وليس
    نموذج Team منفصل) عمداً، حفاظاً على بساطة هذا المشروع النظيف كما طلبت
    (3 نماذج فقط: Match, News, Channel)."""

    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'لم تبدأ بعد'
        LIVE = 'live', 'مباشر الآن'
        FINISHED = 'finished', 'انتهت'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    home_team = models.CharField('الفريق المضيف', max_length=100)
    away_team = models.CharField('الفريق الضيف', max_length=100)
    home_team_logo_url = models.URLField('شعار الفريق المضيف (رابط خارجي)', blank=True, null=True)
    away_team_logo_url = models.URLField('شعار الفريق الضيف (رابط خارجي)', blank=True, null=True)

    competition = models.CharField('البطولة/الدوري', max_length=150, blank=True)

    channel = models.ForeignKey(
        Channel, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matches', verbose_name='قناة البث',
    )

    # رابط بث مباشر خاص بهذه المباراة تحديداً — منفصل عن نظام StreamSource
    # (قائمة روابط failover لكل قناة دائمة)، لأن هذا رابط لمباراة واحدة
    # فقط. يُملأ يدوياً من صفحة التعديل، أو عبر دمج ملف روابط بث في
    # الاستيراد الجماعي (راجع apps/core/bulk_import.py).
    stream_url = models.URLField('رابط البث المباشر (خاص بالمباراة)', max_length=1000, blank=True, null=True)

    match_datetime = models.DateTimeField('موعد المباراة', db_index=True)
    status = models.CharField('الحالة', max_length=10, choices=Status.choices, default=Status.UPCOMING)

    home_score = models.PositiveSmallIntegerField('أهداف المضيف', default=0)
    away_score = models.PositiveSmallIntegerField('أهداف الضيف', default=0)
    elapsed_minutes = models.PositiveSmallIntegerField('الدقيقة الحالية', default=0)

    # مفتاح الربط مع مزوّد البيانات الخارجي — يمنع التكرار عند كل تشغيل
    # لأمر sync_data (upsert عبر external_id، وليس إنشاء دائم)
    external_id = models.CharField(
        'المعرّف الخارجي', max_length=64, blank=True, null=True, unique=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'مباراة'
        verbose_name_plural = 'المباريات'
        ordering = ['match_datetime']
        indexes = [
            # الاستعلام الأشيع من تطبيق Flutter: "أعطني المباريات المباشرة
            # الآن" — فهرس على status وحده يخدم هذا مباشرة
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.home_team} vs {self.away_team} ({self.match_datetime:%Y-%m-%d %H:%M})'


class News(TimeStampedModel):
    """خبر رياضي — يُسحب تلقائياً من RSS عبر sync_data، أو يُكتب يدوياً.
    دورة حياة مطابقة لـ Match عمداً (Scheduled -> Published -> Archived
    بدل Upcoming -> Live -> Finished) — نفس فلسفة إدارة الحالة، بحيث يكون
    قسما "المباريات" و"الأخبار" في لوحة الإدارة متماثلين تماماً."""

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'مجدول'
        PUBLISHED = 'published', 'منشور'
        ARCHIVED = 'archived', 'مؤرشف'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField('العنوان', max_length=250)
    content = models.TextField('المحتوى')
    image = models.ImageField('صورة الخبر (رفع يدوي)', upload_to='news/images/', blank=True, null=True)
    external_image_url = models.URLField('رابط صورة خارجي', max_length=500, blank=True, null=True)

    source_url = models.URLField(
        'رابط المصدر', max_length=500, blank=True, null=True, unique=True,
        help_text='مفتاح فريد لمنع تكرار نفس الخبر عند إعادة تشغيل sync_data',
    )

    related_match = models.ForeignKey(
        Match, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='news_items', verbose_name='مرتبط بمباراة',
    )

    status = models.CharField('الحالة', max_length=10, choices=Status.choices, default=Status.PUBLISHED)
    publish_at = models.DateTimeField(
        'وقت النشر المجدول', null=True, blank=True,
        help_text='اختياري — إن ضُبط وكانت الحالة "مجدول"، يُنشَر الخبر تلقائياً عند هذا الوقت.',
    )
    archive_at = models.DateTimeField(
        'وقت الأرشفة التلقائية', null=True, blank=True,
        help_text='اختياري — إن ضُبط، يُنقَل الخبر تلقائياً لـ"مؤرشف" عند هذا الوقت.',
    )

    class Meta:
        verbose_name = 'خبر'
        verbose_name_plural = 'الأخبار'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title


class SiteSettings(models.Model):
    """
    صف وحيد فقط (Singleton) — مكان مركزي لشعار الموقع، يُقرأ من كل من
    /admin/ (عبر UNFOLD['SITE_LOGO'] في settings.py) و/dashboard/، حتى لا
    يُرفع الشعار مرتين في مكانين منفصلين.
    """
    logo = models.ImageField('شعار الموقع', upload_to='site/', blank=True, null=True)

    # إعدادات شبكات الإعلانات — تُقرأ من تطبيق Flutter عبر /api/app-config/
    # حتى يمكن تغيير معرّفات الإعلانات وتفعيل/تعطيل كل شبكة على حدة دون
    # إصدار تحديث جديد للتطبيق. مفتاح رئيسي (ads_enabled) يُطفئ كل
    # الإعلانات دفعة واحدة، بالإضافة لمفتاح مستقل لكل شبكة.
    ads_enabled = models.BooleanField('تفعيل الإعلانات في التطبيق (المفتاح الرئيسي)', default=False)

    admob_enabled = models.BooleanField('تفعيل AdMob', default=False)
    admob_app_id = models.CharField('AdMob — معرّف التطبيق (App ID)', max_length=100, blank=True)
    admob_banner_ad_unit_id = models.CharField('AdMob — معرّف إعلان البانر (Banner)', max_length=100, blank=True)
    admob_interstitial_ad_unit_id = models.CharField(
        'AdMob — معرّف الإعلان البيني (Interstitial)', max_length=100, blank=True,
    )
    admob_rewarded_ad_unit_id = models.CharField(
        'AdMob — معرّف الإعلان المكافأ (Rewarded)', max_length=100, blank=True,
    )

    facebook_ads_enabled = models.BooleanField('تفعيل Meta / Facebook Audience Network', default=False)
    facebook_ads_placement_id = models.CharField(
        'Facebook Audience Network — معرّف موضع البانر (Banner)', max_length=100, blank=True,
    )
    facebook_ads_interstitial_placement_id = models.CharField(
        'Facebook Audience Network — معرّف موضع الإعلان البيني (Interstitial)', max_length=100, blank=True,
    )
    facebook_ads_rewarded_placement_id = models.CharField(
        'Facebook Audience Network — معرّف موضع الإعلان المكافأ (Rewarded)', max_length=100, blank=True,
    )

    # شبكة إعلانية إضافية عامة (Unity Ads / AppLovin / أي شركة أخرى) — اسم
    # الشبكة نص حر يُدخله المستخدم بنفسه بدل حصر الخيار بشركة واحدة بعينها
    other_ads_enabled = models.BooleanField('تفعيل شبكة إعلانية أخرى', default=False)
    other_ad_network_name = models.CharField('اسم الشبكة الإعلانية الأخرى', max_length=100, blank=True)
    other_ad_banner_id = models.CharField('الشبكة الأخرى — معرّف إعلان البانر (Banner)', max_length=100, blank=True)
    other_ad_interstitial_id = models.CharField(
        'الشبكة الأخرى — معرّف الإعلان البيني (Interstitial)', max_length=100, blank=True,
    )
    other_ad_rewarded_id = models.CharField(
        'الشبكة الأخرى — معرّف الإعلان المكافأ (Rewarded)', max_length=100, blank=True,
    )

    # ملف app-ads.txt — تتحقق منه شبكات الإعلانات (AdMob وغيرها) عبر
    # زحفها الدوري لتأكيد أن هذا الموقع مخوَّل فعلاً ببيع إعلانات لحسابكم
    # الإعلاني؛ بدونه تنخفض تعبئة الإعلانات (Fill Rate) كثيراً أو تنعدم،
    # خصوصاً لحساب AdMob جديد. يُقدَّم من جذر النطاق مباشرة (راجع
    # config/urls.py + apps/core/views.py: app_ads_txt) — وليس من مسار
    # فرعي، لأن أدوات الزحف تبحث عن <domain>/app-ads.txt تحديداً.
    app_ads_txt = models.TextField(
        'محتوى ملف app-ads.txt', blank=True,
        help_text='سطر واحد لكل شبكة إعلانية، بالصيغة التي تعطيها لك الشبكة نفسها '
                   '(مثال من AdMob: google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0)',
    )

    class Meta:
        verbose_name = 'إعدادات الموقع'
        verbose_name_plural = 'إعدادات الموقع'

    def __str__(self):
        return 'إعدادات الموقع'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # لا يُحذف الصف الوحيد أبداً — فقط يُعدَّل

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class IntegrationHealth(models.Model):
    """
    حالة آخر محاولة اتصال فعلية بمزوّد بيانات خارجي (RapidAPI حالياً) —
    صف واحد لكل مصدر (`key` فريد)، يُحدَّثه sync_data.py مع كل محاولة
    مزامنة (ناجحة أو فاشلة)، ويُقرأ من /dashboard/ لعرض تنبيه واضح بدل
    ترك فشل صامت لا يظهر إلا في سجلات الـ worker.
    """
    key = models.CharField('المعرّف', max_length=50, unique=True)
    label = models.CharField('الاسم المعروض', max_length=100)
    is_healthy = models.BooleanField('متصل بنجاح؟', default=True)
    last_checked_at = models.DateTimeField('آخر محاولة', null=True, blank=True)
    last_success_at = models.DateTimeField('آخر نجاح', null=True, blank=True)
    last_error = models.TextField('آخر رسالة خطأ', blank=True)

    class Meta:
        verbose_name = 'حالة تكامل خارجي'
        verbose_name_plural = 'حالة التكاملات الخارجية'

    def __str__(self):
        return self.label

    @classmethod
    def record_success(cls, key, label):
        now = timezone.now()
        cls.objects.update_or_create(
            key=key,
            defaults={'label': label, 'is_healthy': True, 'last_checked_at': now, 'last_success_at': now, 'last_error': ''},
        )

    @classmethod
    def record_failure(cls, key, label, error_message):
        cls.objects.update_or_create(
            key=key,
            defaults={'label': label, 'is_healthy': False, 'last_checked_at': timezone.now(), 'last_error': str(error_message)[:2000]},
        )
