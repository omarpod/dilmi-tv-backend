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
    stream_url = models.URLField('رابط البث (M3U8/HLS)', max_length=500)
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
    """خبر رياضي — يُسحب تلقائياً من RSS عبر sync_data، أو يُكتب يدوياً."""

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

    is_published = models.BooleanField('منشور؟', default=True, db_index=True)

    class Meta:
        verbose_name = 'خبر'
        verbose_name_plural = 'الأخبار'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', '-created_at']),
        ]

    def __str__(self):
        return self.title
