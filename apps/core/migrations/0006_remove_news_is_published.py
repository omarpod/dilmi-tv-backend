from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_news_status_lifecycle'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='news',
            name='core_news_is_publ_ce555a_idx',
        ),
        migrations.RemoveField(
            model_name='news',
            name='is_published',
        ),
        migrations.AddIndex(
            model_name='news',
            index=models.Index(fields=['status', '-created_at'], name='core_news_status_ea0473_idx'),
        ),
    ]
