"""
apps/core/integrations/rss_news.py
--------------------------------------
سحب أخبار رياضية من مصادر RSS. لم أستطع التحقق من عمل خلاصة RSS فعلية
تابعة لموقع رياضي عربي محدد (كووورة/يلاكورة/في الجول) بشكل مباشر — نفس
المشكلة التي واجهتها مع توثيق RapidAPI: هذه المواقع تحجب أدوات الجلب
الآلي (403) عند فتح صفحاتها من هنا.

لذلك المصدر الافتراضي هو خلاصة بحث Google News (نمط رابط مُوثَّق ومستقر
رسمياً من Google، وليس تخميناً لبنية موقع ناشر واحد) مضبوطة على استعلام
"كرة القدم" بالعربية — تُجمِّع أخباراً من نفس المواقع (كووورة، يلاكورة،
في الجول، beIN...) دون الاعتماد على استقرار خلاصة ناشر واحد بعينه.

يمكن استبدالها أو إضافة خلاصات أخرى بالكامل عبر متغير البيئة
NEWS_RSS_FEED_URLS (مفصولة بفواصل) دون لمس هذا الملف.
"""
import html
import re

import feedparser

_USER_AGENT = 'Mozilla/5.0 (compatible; DilmiTVBot/1.0; +https://dilmi.tv)'
_IMG_TAG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']')
_TAG_RE = re.compile(r'<[^<]+?>')


def fetch_entries(feed_url, timeout=15):
    parsed = feedparser.parse(feed_url, agent=_USER_AGENT, request_headers={'User-Agent': _USER_AGENT})
    return parsed.entries or []


def extract_image_url(entry):
    for key in ('media_content', 'media_thumbnail'):
        items = entry.get(key)
        if items:
            url = items[0].get('url')
            if url:
                return url

    for enclosure in entry.get('enclosures', []):
        if 'image' in (enclosure.get('type') or ''):
            return enclosure.get('href') or enclosure.get('url')

    html_blob = entry.get('summary', '') or (
        entry['content'][0].get('value', '') if entry.get('content') else ''
    )
    match = _IMG_TAG_RE.search(html_blob)
    return match.group(1) if match else None


def extract_plain_text(entry):
    raw = entry.get('summary', '') or (
        entry['content'][0].get('value', '') if entry.get('content') else ''
    )
    return html.unescape(_TAG_RE.sub('', raw)).strip()
