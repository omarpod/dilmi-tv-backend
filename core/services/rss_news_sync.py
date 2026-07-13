"""
rss_news_sync.py
------------------
يسحب أخباراً رياضية من مصدر RSS خارجي ويحوّلها لسجلات News محلية، بنفس
أسلوب الحماية (upsert آمن عبر source_url، معالجة أخطاء دفاعية) المُتبَع
في match_sync.py — بديل مجاني ومستقر عن API أخبار مدفوع، بما أن مزود
المباريات الحالي (Free API Live Football Data) لا يوفّر أخباراً إطلاقاً.

== كيف تُغيّر مصدر الأخبار؟ ==
عبر متغير بيئة RSS_NEWS_FEED_URL (راجع settings.py)، بدون لمس هذا
الملف إطلاقاً.
"""
import logging

import feedparser
from django.conf import settings

from core.models import News

logger = logging.getLogger(__name__)


def sync_news_from_rss(feed_url=None):
    """
    نقطة الدخول الرئيسية: يقرأ خلاصة RSS ويُنشئ سجل News لكل عنصر جديد
    (يتخطّى العناصر الموجودة مسبقاً تلقائياً عبر source_url الفريد).
    يُرجع قائمة بكل سجلات News التي أُنشئت حديثاً فقط.
    """
    url = feed_url or settings.RSS_NEWS_FEED_URL

    try:
        parsed_feed = feedparser.parse(url)
    except Exception as e:
        logger.error('فشل تحليل خلاصة RSS من %s: %s', url, e, exc_info=True)
        return []

    if getattr(parsed_feed, 'bozo', False) and not parsed_feed.entries:
        logger.warning(
            'خلاصة RSS من %s تبدو تالفة أو غير قابلة للقراءة: %s',
            url, getattr(parsed_feed, 'bozo_exception', 'سبب غير معروف'),
        )
        return []

    new_articles = []
    for entry in parsed_feed.entries:
        article = _sync_single_entry(entry)
        if article:
            new_articles.append(article)

    return new_articles


def _sync_single_entry(entry):
    """يُزامن عنصر خبر واحد. يُرجع News فقط إن كان جديداً فعلاً."""
    link = getattr(entry, 'link', None)
    title = getattr(entry, 'title', None)

    if not link or not title:
        logger.warning('عنصر RSS بدون رابط أو عنوان، تم تخطّيه: %s', str(entry)[:200])
        return None

    if News.objects.filter(source_url=link).exists():
        return None

    content = (
        getattr(entry, 'summary', None)
        or getattr(entry, 'description', None)
        or 'لا يوجد محتوى تفصيلي متاح من المصدر.'
    )

    article = News.objects.create(
        title=title[:200],
        content=content,
        source_url=link,
        is_published=True,
    )

    _log_image_hint_if_available(article, entry)
    return article


def _log_image_hint_if_available(article, entry):
    """
    محاولة آمنة لملاحظة وجود صورة في RSS (بدون تحميلها كملف — ذلك
    خارج نطاق هذا الإصلاح). لا ترمي أي استثناء أبداً؛ فشل هذا الجزء
    لا يجب أن يمنع حفظ الخبر نفسه بنجاح.
    """
    try:
        media_content = getattr(entry, 'media_content', None)
        if media_content and isinstance(media_content, list) and media_content:
            image_url = media_content[0].get('url')
            if image_url:
                logger.info(
                    'خبر "%s" له صورة في RSS (%s) — أضفها يدوياً من /admin/ إن رغبت.',
                    article.title, image_url,
                )
    except Exception:
        pass
