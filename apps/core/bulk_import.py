"""
apps/core/bulk_import.py
---------------------------
استيراد جماعي يدوي بالكامل لجدول مباريات — من ملف CSV أو JSON يرفعه
المستخدم عبر /dashboard/matches/bulk-import/. لا يتصل بأي مصدر خارجي:
كل البيانات منسوخة يدوياً من طرف المستخدم قبل الرفع، هذا الملف فقط
يقرأ الملف ويحدّث قاعدة البيانات.

صيغة الملف المتوقعة — أعمدة/مفاتيح مرنة (عربي أو إنجليزي)، أي ترتيب:
- الفريقان: عمودان منفصلان (home_team/away_team أو الفريق_المضيف/
  الفريق_الضيف)، أو عمود واحد لاسم المباراة كاملاً (مثل "الأهلي vs
  الزمالك" أو "الأهلي ضد الزمالك") يُقسَّم تلقائياً.
- البطولة: اختياري (competition/league/البطولة).
- الموعد: أي صيغة تاريخ/وقت مفهومة تقريباً (date/match_datetime/
  التاريخ/الموعد) — يُحلَّل عبر python-dateutil بافتراض يوم/شهر/سنة
  (dayfirst) المتوافق مع المنطقة العربية، وليس شهر/يوم/سنة الأمريكي.
- شعارا الفريقين: اختياري (home_team_logo_url/away_team_logo_url أو
  شعار_المضيف/شعار_الضيف).
- النتيجة الحالية: اختياري (home_score/away_score أو نتيجة_المضيف/
  نتيجة_الضيف) — هذا هو أسلوب "تحديث النتيجة" في هذا النظام: أعد نسخ
  الجدول (بما فيه النتيجة الحالية) من مصدرك وأعد رفع نفس الملف؛ التحديث
  يظهر خلال ثوانٍ. لا يوجد جلب تلقائي للنتيجة من أي مصدر خارجي — راجع
  رد المحادثة لسبب عدم بناء ذلك.

تجنّب التكرار: Match.objects.update_or_create() بمفتاح (home_team,
away_team, match_datetime) — نفس المباراة بنفس الفريقين ونفس التوقيت
تُحدَّث بدل تكرارها؛ رفع نفس الملف مرتين آمن تماماً. الحقول الاختيارية
(الشعاران والنتيجة) تُحدَّث فقط إن وُجدت فعلياً في الصف — عمود غائب لا
يمسح قيمة موجودة مسبقاً (مثال: رفع جدول بلا أعمدة نتيجة لا يُصفّر نتيجة
مباراة مباشرة بالفعل). الحالة (status) لا تُضبط من الملف إطلاقاً — نظام
منفصل تلقائي بالكامل يعتمد على الوقت (راجع apps/core/tasks.py).
"""
import csv
import io
import json
import re

from dateutil import parser as dateutil_parser
from django.utils import timezone

from .models import Match

MAX_ROWS = 500

_HOME_TEAM_KEYS = ['home_team', 'home', 'الفريق_المضيف', 'المضيف', 'فريق1', 'الفريق_الاول', 'الفريق_الأول']
_AWAY_TEAM_KEYS = ['away_team', 'away', 'الفريق_الضيف', 'الضيف', 'فريق2', 'الفريق_الثاني']
_MATCH_NAME_KEYS = ['match', 'teams', 'اسم_المباراة', 'المباراة']
_COMPETITION_KEYS = ['competition', 'league', 'tournament', 'البطولة', 'الدوري']
_DATETIME_KEYS = [
    'match_datetime', 'datetime', 'date', 'time',
    'التاريخ', 'الوقت', 'تاريخ_المباراة', 'موعد_المباراة', 'الموعد',
]
_HOME_LOGO_KEYS = ['home_team_logo_url', 'home_logo', 'شعار_المضيف', 'شعار_الفريق_المضيف']
_AWAY_LOGO_KEYS = ['away_team_logo_url', 'away_logo', 'شعار_الضيف', 'شعار_الفريق_الضيف']
_HOME_SCORE_KEYS = ['home_score', 'نتيجة_المضيف', 'اهداف_المضيف', 'أهداف_المضيف']
_AWAY_SCORE_KEYS = ['away_score', 'نتيجة_الضيف', 'اهداف_الضيف', 'أهداف_الضيف']

_NAME_SEPARATORS = [' vs ', ' VS ', ' Vs ', ' × ', ' ضد ', ' - ', ' – ', ' — ']


class BulkImportError(Exception):
    """خطأ في صيغة الملف نفسه (وليس صف واحد) — يوقف العملية بالكامل."""


class RowError(Exception):
    """خطأ في صف واحد فقط — الصفوف الأخرى تُكمل معالجتها."""


class ImportResult:
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.row_errors = []  # [(line_number, raw_row, message), ...]

    @property
    def total_ok(self):
        return self.created + self.updated


def _normalize_key(key):
    return re.sub(r'\s+', '_', (key or '').strip().lower())


def _find_value(row, candidate_keys):
    normalized_row = {_normalize_key(k): v for k, v in row.items()}
    for key in candidate_keys:
        value = normalized_row.get(_normalize_key(key))
        if value not in (None, ''):
            return value.strip() if isinstance(value, str) else value
    return None


def _split_match_name(name):
    for sep in _NAME_SEPARATORS:
        parts = re.split(re.escape(sep.strip()), name, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            return parts[0].strip(), parts[1].strip()
    return None, None


def _parse_row(row):
    home = _find_value(row, _HOME_TEAM_KEYS)
    away = _find_value(row, _AWAY_TEAM_KEYS)

    if not home or not away:
        match_name = _find_value(row, _MATCH_NAME_KEYS)
        if match_name:
            home, away = _split_match_name(match_name)

    if not home or not away:
        raise RowError('تعذّر تحديد اسمَي الفريقين (تحقّق من أعمدة home_team/away_team أو عمود اسم المباراة)')

    competition = _find_value(row, _COMPETITION_KEYS) or ''

    datetime_raw = _find_value(row, _DATETIME_KEYS)
    if not datetime_raw:
        raise RowError('حقل الموعد (التاريخ/الوقت) مفقود')

    try:
        match_datetime = dateutil_parser.parse(str(datetime_raw), dayfirst=True)
    except (ValueError, OverflowError, TypeError):
        raise RowError(f'تعذّر فهم صيغة التاريخ/الوقت: "{datetime_raw}"')

    if timezone.is_naive(match_datetime):
        match_datetime = timezone.make_aware(match_datetime, timezone.get_current_timezone())

    parsed = {
        'home_team': home,
        'away_team': away,
        'match_datetime': match_datetime,
        'defaults': {'competition': competition},
    }

    home_logo = _find_value(row, _HOME_LOGO_KEYS)
    if home_logo:
        parsed['defaults']['home_team_logo_url'] = home_logo

    away_logo = _find_value(row, _AWAY_LOGO_KEYS)
    if away_logo:
        parsed['defaults']['away_team_logo_url'] = away_logo

    home_score = _find_value(row, _HOME_SCORE_KEYS)
    if home_score is not None:
        try:
            parsed['defaults']['home_score'] = int(home_score)
        except (ValueError, TypeError):
            pass  # قيمة نتيجة غير صالحة — تُتجاهَل بصمت، لا تُفشل الصف كاملاً

    away_score = _find_value(row, _AWAY_SCORE_KEYS)
    if away_score is not None:
        try:
            parsed['defaults']['away_score'] = int(away_score)
        except (ValueError, TypeError):
            pass

    return parsed


def _iter_rows(raw_bytes, filename):
    lower_name = (filename or '').lower()

    if lower_name.endswith('.json'):
        try:
            data = json.loads(raw_bytes.decode('utf-8-sig'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise BulkImportError(f'ملف JSON غير صالح: {e}')
        if not isinstance(data, list):
            raise BulkImportError('ملف JSON يجب أن يحتوي قائمة (JSON array) من المباريات.')
        for index, row in enumerate(data, start=1):
            if not isinstance(row, dict):
                raise BulkImportError(f'العنصر رقم {index} في ملف JSON ليس كائناً (object).')
            yield index, row
        return

    # CSV افتراضياً (بما في ذلك .txt المنسوخ يدوياً بفواصل) — utf-8-sig
    # يتجاهل BOM الذي يضيفه Excel تلقائياً عند تصدير CSV
    try:
        text = raw_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise BulkImportError('تعذّرت قراءة الملف كنص UTF-8 — تأكد أن الملف محفوظ بترميز UTF-8.')

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise BulkImportError('الملف فارغ أو بلا صف عناوين أعمدة (Header).')

    for index, row in enumerate(reader, start=2):  # الصف 1 هو العناوين
        if not any((v or '').strip() for v in row.values()):
            continue  # صف فارغ تماماً (شائع كسطر أخير) — يُتجاهَل بصمت
        yield index, row


def run_bulk_import(raw_bytes, filename):
    result = ImportResult()
    rows = list(_iter_rows(raw_bytes, filename))

    if len(rows) > MAX_ROWS:
        raise BulkImportError(f'الملف يحتوي {len(rows)} صفاً — الحد الأقصى لكل رفعة هو {MAX_ROWS}.')

    for line_number, raw_row in rows:
        try:
            parsed = _parse_row(raw_row)
        except RowError as e:
            result.row_errors.append((line_number, raw_row, str(e)))
            continue

        _, created = Match.objects.update_or_create(
            home_team=parsed['home_team'],
            away_team=parsed['away_team'],
            match_datetime=parsed['match_datetime'],
            defaults=parsed['defaults'],
        )
        if created:
            result.created += 1
        else:
            result.updated += 1

    return result
