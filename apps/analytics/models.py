"""
apps/analytics/models.py
--------------------------
تتبّع حقيقي (وليس أرقاماً وهمية) لعدد المشاهدين المباشرين — يعتمد على أن
يستدعي تطبيق العميل (Flutter) نقطة /api/viewers/heartbeat/ كل 30 ثانية
تقريباً أثناء تشغيل أي بث. بدون هذا الاستدعاء من العميل، تبقى الأرقام صفراً
بصدق (ولا نُخفي ذلك خلف رقم مُصطنع).
"""
import uuid

from django.db import models

from apps.core.models import Channel, Match


class Platform(models.TextChoices):
    PHONE = 'phone', 'هاتف'
    TABLET = 'tablet', 'جهاز لوحي'
    TV = 'tv', 'شاشة ذكية'
    WEB = 'web', 'متصفح'
    OTHER = 'other', 'أخرى'


class ViewerSession(models.Model):
    """
    "من يُشاهد الآن؟" — سطر واحد لكل (جهاز × قناة/مباراة)، يُحدَّث (upsert)
    عند كل heartbeat بدل إدراج سطر جديد في كل مرة، لإبقاء الجدول بحجم
    عدد المشاهدين الفعليين وليس عدد النبضات.
    """
    device_id = models.CharField('معرّف الجهاز', max_length=64, db_index=True)
    platform = models.CharField('المنصة', max_length=10, choices=Platform.choices, default=Platform.OTHER)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True, related_name='viewer_sessions')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True, related_name='viewer_sessions')
    first_seen = models.DateTimeField('أول ظهور', auto_now_add=True)
    last_seen = models.DateTimeField('آخر نبضة', auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'جلسة مشاهدة'
        verbose_name_plural = 'جلسات المشاهدة'
        constraints = [
            models.UniqueConstraint(
                fields=['device_id', 'channel', 'match'],
                name='unique_device_target',
            ),
        ]
        indexes = [
            models.Index(fields=['last_seen']),
        ]


class ViewerSnapshot(models.Model):
    """
    لقطة دورية (كل بضع دقائق عبر Railway Cron) لعدد المشاهدين الإجمالي —
    هذه هي البيانات التي يُبنى منها خط الاتجاه (Sparkline) في اللوحة.
    بدون هذا الجدول، لا نملك أي تاريخ لرسم اتجاه — فقط اللحظة الحالية.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    taken_at = models.DateTimeField('وقت اللقطة', auto_now_add=True, db_index=True)
    live_viewers = models.PositiveIntegerField('عدد المشاهدين', default=0)

    class Meta:
        verbose_name = 'لقطة مشاهدين'
        verbose_name_plural = 'لقطات المشاهدين'
        ordering = ['-taken_at']
