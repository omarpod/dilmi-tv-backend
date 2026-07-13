"""
sync_news.py
-------------
أمر إدارة يدوي لسحب الأخبار الرياضية من خلاصة RSS (بديل مجاني ومستقر
عن API أخبار مدفوع). يعمل الآن بدون أي حاجة لـ Celery/Redis، بنفس
فلسفة sync_matches تماماً.

الاستخدام:
    python manage.py sync_news
"""
from django.core.management.base import BaseCommand

from core.services.rss_news_sync import sync_news_from_rss


class Command(BaseCommand):
    help = 'يسحب أخباراً رياضية جديدة من خلاصة RSS (راجع RSS_NEWS_FEED_URL في settings.py).'

    def handle(self, *args, **options):
        new_articles = sync_news_from_rss()

        if new_articles:
            self.stdout.write(self.style.SUCCESS(f'تمت إضافة {len(new_articles)} خبر جديد:'))
            for article in new_articles:
                self.stdout.write(f'  - {article.title}')
        else:
            self.stdout.write(self.style.WARNING(
                'لم يُضَف أي خبر جديد (إما لا توجد أخبار جديدة في الخلاصة، '
                'أو فشل الاتصال — راجع السجل أعلاه للتفاصيل).'
            ))
