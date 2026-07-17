"""
apps/streaming/models.py
-------------------------
StreamSource يستبدل Channel.stream_url القديم (رابط واحد فقط) بقائمة
روابط مرتّبة بالأولوية لكل قناة — الأساس الذي يقوم عليه الفشل التلقائي
(Native Failover) في تطبيق Flutter: عند تعطّل الرابط الأساسي، يجرّب
التطبيق تلقائياً التالي في القائمة دون أي تدخل من المستخدم.

كل الروابط هنا تُضاف يدوياً (لوحة التحكم) — القناة تملك حقوق بثها أو
رخّصته، والفحص الدوري في tasks.py لا يفعل أكثر من طلب HEAD بسيط على
روابط مضافة أصلاً من طرفكم، فلا حاجة لأي Proxy أو تمويه بصمة هنا.
"""
from django.db import models

FAILURE_THRESHOLD = 3  # بعد هذا العدد من الفحوصات الفاشلة المتتالية، يُعطَّل الرابط تلقائياً


class StreamSource(models.Model):
    channel = models.ForeignKey(
        'core.Channel', on_delete=models.CASCADE, related_name='sources',
        verbose_name='القناة',
    )
    url = models.URLField('الرابط', max_length=1000)
    label = models.CharField(
        'تسمية', max_length=100, blank=True,
        help_text='مثال: HD، احتياطي 1... (اختياري، لتمييز الرابط فقط)',
    )
    priority = models.PositiveSmallIntegerField(
        'الأولوية', default=0,
        help_text='0 = يُجرَّب أولاً. الأرقام الأصغر لها أولوية أعلى.',
    )

    is_active = models.BooleanField(
        'نشِط؟', default=True,
        help_text='يُعطَّل تلقائياً بعد عدة فحوصات فاشلة متتالية، أو يدوياً من هنا.',
    )
    is_healthy = models.BooleanField('سليم في آخر فحص؟', default=True, editable=False)
    consecutive_failures = models.PositiveSmallIntegerField('فحوصات فاشلة متتالية', default=0, editable=False)
    last_checked_at = models.DateTimeField('آخر فحص', null=True, blank=True, editable=False)

    created_at = models.DateTimeField('تاريخ الإضافة', auto_now_add=True)

    class Meta:
        verbose_name = 'رابط بث'
        verbose_name_plural = 'روابط البث'
        ordering = ['priority', '-is_healthy', 'created_at']
        indexes = [
            models.Index(fields=['channel', 'is_active', 'priority']),
        ]

    def __str__(self):
        return f'{self.channel.name} — {self.label or self.url[:40]}'
