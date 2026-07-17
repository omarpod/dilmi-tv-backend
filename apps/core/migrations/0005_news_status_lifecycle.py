# يضيف حقول دورة الحياة الجديدة وينقل بيانات is_published القديمة إليها
# — قبل حذف الحقل القديم في الهجرة التالية 0006، حفاظاً على نفس أسلوب
# الهجرة الآمنة المُستخدَم مع StreamSource (إضافة + نقل بيانات، ثم حذف).
from django.db import migrations, models


def migrate_is_published_forward(apps, schema_editor):
    News = apps.get_model('core', 'News')
    News.objects.filter(is_published=True).update(status='published')
    News.objects.filter(is_published=False).update(status='scheduled')


def migrate_is_published_backward(apps, schema_editor):
    News = apps.get_model('core', 'News')
    News.objects.filter(status='published').update(is_published=True)
    News.objects.exclude(status='published').update(is_published=False)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_channel_stream_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='archive_at',
            field=models.DateTimeField(
                blank=True,
                help_text='اختياري — إن ضُبط، يُنقَل الخبر تلقائياً لـ"مؤرشف" عند هذا الوقت.',
                null=True,
                verbose_name='وقت الأرشفة التلقائية',
            ),
        ),
        migrations.AddField(
            model_name='news',
            name='publish_at',
            field=models.DateTimeField(
                blank=True,
                help_text='اختياري — إن ضُبط وكانت الحالة "مجدول"، يُنشَر الخبر تلقائياً عند هذا الوقت.',
                null=True,
                verbose_name='وقت النشر المجدول',
            ),
        ),
        migrations.AddField(
            model_name='news',
            name='status',
            field=models.CharField(
                choices=[('scheduled', 'مجدول'), ('published', 'منشور'), ('archived', 'مؤرشف')],
                default='published',
                max_length=10,
                verbose_name='الحالة',
            ),
        ),
        migrations.RunPython(migrate_is_published_forward, migrate_is_published_backward),
    ]
