# هجرة بيانات (وليس تعديل هيكل) — تنقل كل Channel.stream_url غير الفارغ
# إلى StreamSource جديد بأولوية 0، قبل حذف الحقل القديم نهائياً في
# الهجرة التالية 0004. يجب أن تُنفَّذ بعد إنشاء جدول StreamSource
# (streaming.0001_initial) وقبل حذف الحقل القديم.
from django.db import migrations


def migrate_stream_urls_forward(apps, schema_editor):
    Channel = apps.get_model('core', 'Channel')
    StreamSource = apps.get_model('streaming', 'StreamSource')

    for channel in Channel.objects.exclude(stream_url=''):
        StreamSource.objects.create(channel=channel, url=channel.stream_url, priority=0)


def migrate_stream_urls_backward(apps, schema_editor):
    Channel = apps.get_model('core', 'Channel')
    StreamSource = apps.get_model('streaming', 'StreamSource')

    for channel in Channel.objects.all():
        first_source = StreamSource.objects.filter(channel=channel).order_by('priority').first()
        if first_source:
            channel.stream_url = first_source.url
            channel.save(update_fields=['stream_url'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_sitesettings'),
        ('streaming', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_stream_urls_forward, migrate_stream_urls_backward),
    ]
