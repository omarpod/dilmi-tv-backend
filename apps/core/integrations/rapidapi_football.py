"""
apps/core/integrations/rapidapi_football.py
------------------------------------------------
عميل واجهة "Free API Live Football Data" على RapidAPI. مسؤوليته الوحيدة:
جلب القائمة الخام للمباريات المباشرة كما هي — أي تفسير/تحويل لحقول Match
يتم في sync_data.py عمداً، حتى يبقى هذا الملف بسيطاً وقابلاً لإعادة
الاستخدام أو الاستبدال بمزوّد آخر لاحقاً دون لمس منطق قاعدة البيانات.

ملاحظة أمانة مهمة: لم أتمكن من الوصول لتوثيق شكل الاستجابة الدقيق لهذا
الـ Endpoint تحديداً (صفحات توثيق RapidAPI تحجب الجلب الآلي دون تسجيل
دخول). دالة fetch_live_matches لا تفترض عمقاً أو غلافاً ثابتاً — تبحث في
كامل بنية الاستجابة (بغضّ النظر عن عمق التداخل، بما فيه حالة التجميع حسب
الدوري) عن القائمة التي تحتوي فعلاً سجلات تشبه مباريات (مفاتيح مثل
homeTeam/awayTeam/goals). إن فشل هذا التخمين، الخطأ الناتج يطبع خريطة
كاملة لبنية الاستجابة (بدون قيم حساسة) تكفي لتصحيح المنطق دفعة واحدة.
"""
import requests

RAPIDAPI_HOST = 'free-api-live-football-data.p.rapidapi.com'
LIVE_MATCHES_URL = f'https://{RAPIDAPI_HOST}/football-current-live'
MATCHES_BY_DATE_URL = f'https://{RAPIDAPI_HOST}/football-get-matches-by-date'


class RapidApiFootballError(Exception):
    pass


def _get(url, api_key, params=None, timeout=15):
    response = requests.get(
        url,
        params=params,
        headers={'x-rapidapi-key': api_key, 'x-rapidapi-host': RAPIDAPI_HOST},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _extract_or_raise(payload, source_label):
    matches = _find_matches_list(payload)
    if matches is not None:
        return matches
    raise RapidApiFootballError(
        f'شكل استجابة غير متوقع من {source_label} — '
        f'خريطة الحقول الكاملة: {_describe_shape(payload)}'
    )


# مفاتيح "تلمّح" أن الـ dict هو سجل مباراة فعلي (وليس مجموعة/دوري/غلاف) —
# التطابق غير حساس لحالة الأحرف. يكفي وجود مفتاح واحد منها.
_MATCH_SIGNAL_KEYS = {
    'hometeam', 'awayteam', 'home_team', 'away_team', 'home', 'away', 'teams',
    'homescore', 'awayscore', 'home_score', 'away_score', 'goals', 'score',
    'fixture', 'matchid', 'match_id',
}


def fetch_live_matches(api_key, timeout=15):
    payload = _get(LIVE_MATCHES_URL, api_key, timeout=timeout)
    return _extract_or_raise(payload, 'football-current-live')


def fetch_matches_by_date(api_key, date_str, timeout=15):
    """date_str بصيغة YYYYMMDD (مثال: 20241107) — كما في المثال الذي زوّدتنا به."""
    payload = _get(MATCHES_BY_DATE_URL, api_key, params={'date': date_str}, timeout=timeout)
    return _extract_or_raise(payload, 'football-get-matches-by-date')


def _looks_like_match(node):
    if not isinstance(node, dict):
        return False
    keys = {str(k).lower() for k in node.keys()}
    return bool(keys & _MATCH_SIGNAL_KEYS)


def _collect_lists_by_key(node, key_name=None, out=None):
    """
    يجمع كل القوائم الموجودة في أي عمق (بما فيها الفارغة — رد بلا مباريات
    اليوم شكل صالح تماماً وليس خطأً)، مُصنَّفة حسب اسم المفتاح الذي وُجدت
    تحته — بما يشمل تجميع نفس المفتاح المتكرر عبر عدة مجموعات (مثال شائع:
    قائمة دوريات، كل دوري بداخله matches خاصة به — التجميع هنا يدمج
    matches كل الدوريات معاً بدل أخذ أول دوري فقط).
    """
    if out is None:
        out = {}
    if isinstance(node, list):
        if not node or isinstance(node[0], dict):
            out.setdefault(key_name or '$root', []).extend(node)
        for item in node:
            _collect_lists_by_key(item, key_name, out)
    elif isinstance(node, dict):
        for key, value in node.items():
            _collect_lists_by_key(value, key, out)
    return out


def _find_matches_list(payload):
    """
    بدل افتراض عمق/مفتاح ثابت (سبب فشل المحاولة الأولى: البيانات كانت
    متداخلة أعمق من response مباشرة)، نجمع كل القوائم المرشَّحة أياً كان
    عمقها، ثم نختار المجموعة التي تحتوي أكبر عدد من العناصر "تبدو كمباراة
    فعلاً" (مفاتيح مثل homeTeam/awayTeam/goals...) — وليس أي قائمة عناصرها
    dict بالصدفة (قد تكون قائمة دوريات أو بطولات لا مباريات).

    ترجع None فقط إن لم توجد أي قائمة على الإطلاق في الاستجابة (شكل غير
    مفهوم كلياً، يستحق رفع خطأ)؛ ترجع [] لرد لا يحتوي مباريات اليوم (حالة
    صالحة وشائعة)، وليس فقط للقوائم غير الفارغة.
    """
    grouped = _collect_lists_by_key(payload)
    if not grouped:
        return None

    scored = sorted(
        (
            (sum(1 for item in items if _looks_like_match(item)), items)
            for items in grouped.values()
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )
    best_score, best_items = scored[0]
    if best_score > 0:
        return best_items
    # لا شيء يبدو كمباراة — لكن إن كانت إحدى القوائم المرشَّحة فارغة أصلاً
    # (وليست قائمة دوريات/بطولات غير فارغة لا تشبه مباريات)، فهذه على
    # الأرجح استجابة صحيحة تعني ببساطة "لا مباريات"
    if any(len(items) == 0 for items in grouped.values()):
        return []
    return None


def _describe_shape(node, path='$', depth=0, max_depth=4):
    """يبني وصفاً مختصراً لبنية الاستجابة (بدون قيم فعلية) لتسهيل تشخيص
    أي فشل مستقبلي في تخمين مكان القائمة دفعة واحدة."""
    if depth >= max_depth:
        return f'{path}: ...'
    if isinstance(node, dict):
        parts = [_describe_shape(v, f'{path}.{k}', depth + 1, max_depth) for k, v in node.items()]
        return '; '.join(parts)
    if isinstance(node, list):
        sample = _describe_shape(node[0], f'{path}[0]', depth + 1, max_depth) if node else ''
        return f'{path}: list(len={len(node)}) {sample}'
    return f'{path}: {type(node).__name__}'
