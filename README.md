# Dilmi TV — لوحة التحكم والـ API (Backend)

مشروع Django كامل لإدارة تطبيق Dilmi TV: القنوات، الفرق، التشكيلات، المباريات،
الأخبار، وإعدادات إعلانات AdMob — مع واجهة API جاهزة يقرأ منها تطبيق الأندرويد.

## 1. التشغيل خطوة بخطوة

```bash
# 1) أنشئ بيئة افتراضية (اختياري لكن مستحسن)
python -m venv venv
source venv/bin/activate        # على ويندوز: venv\Scripts\activate

# 2) ثبّت المكتبات
pip install -r requirements.txt

# 3) أنشئ جداول قاعدة البيانات (SQLite) بناءً على models.py
python manage.py makemigrations core
python manage.py migrate

# 4) أنشئ حساب المدير لدخول لوحة التحكم
python manage.py createsuperuser

# 5) شغّل الخادم محلياً
python manage.py runserver
```

بعدها افتح المتصفح على:
- `http://127.0.0.1:8000/admin/` → لوحة التحكم (أدخل بيانات المدير التي أنشأتها)
- `http://127.0.0.1:8000/api/channels/` → مثال على استجابة الـ API بصيغة JSON

## ⚠️ 1.1 مهم: تحديث السيرفر المنشور على Render

بما أن لوحتك تعمل بالفعل على Render، أضفنا نماذج جديدة (`Analytics`،
`SiteSettings`، `NotificationSubscriber`، `StaticPage`) تحتاج **جداول
جديدة** في قاعدة البيانات. بعد رفع هذا الكود المحدّث لمستودعك:

1. من لوحة تحكم Render، افتح تبويب **Shell** الخاص بخدمتك، ونفّذ:
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   ```
2. **أضف محتوى صفحتي "من نحن" و"سياسة الخصوصية" يدوياً** من `/admin/` ←
   قسم "الصفحات الثابتة" ← أضف سجلّين، أحدهما بـ `slug = privacy_policy`
   والآخر بـ `slug = about_us` — التطبيق سيعرض خطأً واضحاً إذا حاول جلب
   صفحة غير موجودة بعد، وهذا متوقّع حتى تُضيفها أول مرة.

## 1.2 ملاحظة حول Render والملفات المرفوعة (صور المحرر الغني)

الخطة المجانية لـ Render **لا تحفظ الملفات المرفوعة بشكل دائم** (كل صور
`MEDIA_ROOT`، بما فيها صور محرر النصوص الغني، تُحذف عند كل إعادة نشر
`deploy`). لصفحات نصية بسيطة هذا غير مؤثر عادة، لكن إذا أدرجت صوراً
داخل محتوى "من نحن" مثلاً، ستحتاج لاحقاً خدمة تخزين خارجية دائمة (مثل
Cloudinary أو AWS S3) — خارج نطاق هذا التحديث الحالي، أخبرني إن احتجتها.

## 2. روابط الـ API الجاهزة

| الرابط                     | الوصف                                      |
|----------------------------|---------------------------------------------|
| `GET /api/channels/`       | قائمة القنوات المفعّلة                      |
| `GET /api/teams/`          | قائمة الفرق مع لاعبيها                      |
| `GET /api/matches/`        | قائمة المباريات (كل التفاصيل + التشكيلة)    |
| `GET /api/matches/?status=live` | فلترة المباريات المباشرة فقط         |
| `GET /api/news/`           | قائمة الأخبار المنشورة                      |
| `GET /api/ad-settings/`    | إعدادات إعلانات AdMob الحالية                |
| `GET /api/site-settings/`  | روابط التواصل الاجتماعي والبريد             |
| `GET /api/static-pages/privacy_policy/` | محتوى صفحة سياسة الخصوصية (HTML)   |
| `GET /api/static-pages/about_us/` | محتوى صفحة "من نحن" (HTML)           |
| `POST /api/track-visit/`   | تسجيل زيارة جديدة (نظام الإحصائيات)         |
| `POST /api/register-fcm-token/` | تسجيل رمز جهاز لاستقبال إشعارات Push  |

كل روابط `GET` للقراءة فقط من التطبيق. الإضافة والتعديل تتم حصراً من
لوحة تحكم `/admin/`. روابط `POST` الوحيدة هي `track-visit` و
`register-fcm-token`، وهما مصمّمان عمداً ليكتب فيهما التطبيق نفسه.

### أمثلة على الاستخدام

```bash
# تسجيل زيارة (يستدعيها التطبيق عند فتحه)
curl -X POST https://dilmi-tv-backend.onrender.com/api/track-visit/ \
  -H "Content-Type: application/json" \
  -d '{"device": "Android 14 - SM-G991B", "screen": "home"}'

# تسجيل رمز إشعارات جهاز
curl -X POST https://dilmi-tv-backend.onrender.com/api/register-fcm-token/ \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "xxxxxxxx", "device_platform": "android"}'
```

## 3. تطبيق الأندرويد: التوصية والربط بالـ API

**التوصية: Flutter.**

السبب:
- أداء قريب من التطبيقات الأصلية (Native) وواجهات سلسة.
- مكتبة `http` بسيطة جداً لجلب بيانات JSON — تجربة شبيهة بما بنيناه في Django.
- دعم ممتاز وجاهز لإعلانات AdMob عبر حزمة `google_mobile_ads` الرسمية.
- يمكنك لاحقاً نشر نفس الكود على iOS بأقل جهد إضافي.

البديل (Kivy) يبقى ممكناً إن كنت تفضل البقاء كلياً داخل Python، لكن دعمه
لإعلانات AdMob وسلاسة الواجهات أضعف بكثير مقارنة بـ Flutter لتطبيق جماهيري.

### مثال بسيط لجلب المباريات في Flutter (Dart)

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

// عنوان الخادم: أثناء التطوير على المحاكي استخدم 10.0.2.2 بدل 127.0.0.1
const String baseUrl = 'http://10.0.2.2:8000/api';

Future<List<dynamic>> fetchLiveMatches() async {
  final response = await http.get(Uri.parse('$baseUrl/matches/?status=live'));

  if (response.statusCode == 200) {
    // decode: تحويل نص JSON القادم من Django إلى بيانات Dart قابلة للاستخدام
    final data = jsonDecode(utf8.decode(response.bodyBytes));
    return data['results']; // بسبب التصفح (pagination) المفعّل في DRF
  } else {
    throw Exception('فشل جلب المباريات: ${response.statusCode}');
  }
}
```

هكذا يجلب التطبيق البيانات "لحظياً" كل مرة يُفتح فيها أو يُحدَّث فيها الصفحة
(يمكن لاحقاً إضافة تحديث تلقائي كل X ثانية أو Web Sockets لو أردت بثاً حياً أدق).

## 4. خارطة الطريق المقترحة

1. **الآن:** شغّل المشروع محلياً، أضف بيانات تجريبية عبر `/admin/`، وتأكد أن
   `/api/matches/` يعيد بيانات صحيحة.
2. **بعدها:** ابدأ مشروع Flutter منفصل، واجلب بيانات `/api/channels/` و
   `/api/matches/` وأعرضها في شاشات بسيطة.
3. **ثم:** أضف AdMob في تطبيق Flutter باستخدام معرّفات الإعلانات القادمة
   من `/api/ad-settings/` (بدل تثبيتها داخل كود التطبيق — هكذا تستطيع
   تغيير الإعلانات دون إعادة نشر التطبيق في المتجر!).
4. **قبل النشر الفعلي:**
   - انقل `SECRET_KEY` إلى متغير بيئة (environment variable) بدل كتابته
     مباشرة في `settings.py`.
   - اجعل `DEBUG = False` و `ALLOWED_HOSTS` محددة باسم نطاقك الحقيقي.
   - انتقل من SQLite إلى PostgreSQL إذا كبر عدد المستخدمين (SQLite ممتاز
     للبداية والتعلّم، لكنه محدود عند الحمل الكبير المتزامن).
   - ارفع المشروع على استضافة تدعم Python مثل Railway أو Render أو PythonAnywhere.

## 5. هيكل المشروع

```
dilmi_tv_backend/
├── manage.py
├── requirements.txt
├── templates/
│   └── admin/
│       └── index.html      ← بطاقات الإحصائيات فوق لوحة المعلومات
├── dilmi_tv_backend/       ← إعدادات المشروع العامة
│   ├── settings.py         ← بما فيها JAZZMIN_SETTINGS و JAZZMIN_UI_TWEAKS
│   ├── urls.py
│   └── wsgi.py
└── core/                   ← تطبيقنا: كل منطق Dilmi TV هنا
    ├── models.py           ← تصميم قاعدة البيانات
    ├── admin.py            ← تسجيل النماذج في لوحة التحكم
    ├── apps.py             ← يحقن إحصائيات الداشبورد (ready())
    ├── dashboard.py         ← حساب أرقام بطاقات الإحصائيات
    ├── serializers.py       ← تحويل البيانات إلى JSON
    ├── views.py            ← منطق الـ API
    ├── urls.py             ← روابط الـ API
    └── static/
        ├── images/site_logo.png        ← شعار اللوحة
        └── admin/css/jazzmin_custom.css ← تأثيرات النيون المخصصة
```

## 6. لوحة التحكم الاحترافية (Jazzmin)

اللوحة الآن تستخدم **Jazzmin** بثيم داكن مخصص (Navy/Charcoal + نيون
أخضر مزرق/برتقالي — نفس هوية تطبيق Flutter تماماً) بدل شكل Django
الافتراضي.

### ما تغيّر
- شكل كامل جديد: شريط علوي وقائمة جانبية داكنة، أيقونات مخصصة لكل نموذج
- صفحة تسجيل دخول مصمَّمة بالكامل (خلفية متدرجة + بطاقة توهج + شعار)
- **بطاقات إحصائيات حقيقية** أعلى الصفحة الرئيسية: إجمالي المشاهدات،
  مشاهدات آخر 30 يوماً، المشتركون النشِطون، مباريات مباشرة الآن، القنوات
  المفعّلة، الأخبار المنشورة
- **كل نموذج وميزة كانت موجودة سابقاً لا تزال موجودة بالكامل** — لم
  نستبدل قائمة النماذج، فقط أضفنا البطاقات فوقها

### لماذا كل النماذج ضمن قسم واحد قابل للطي في القائمة الجانبية؟
Jazzmin يُنشئ قسماً منفصلاً تلقائياً **لكل تطبيق Django فعلي مُثبَّت**
(مثل `core`، `auth`). بما أن كل نماذجنا العشرة داخل تطبيق `core` واحد،
تظهر جميعها ضمن قسم واحد قابل للطي (بترتيب منطقي عبر `order_with_respect_to`)
بدل عدة أقسام منفصلة كما في صورتك المرجعية بالضبط. لإنشاء أقسام منفصلة
فعلياً (كل قسم "تطبيق Django" مستقل) يتطلب إعادة هيكلة المشروع لعدة
تطبيقات صغيرة (مثلاً: `channels`، `matches`، `settings_app`) — تغيير أكبر
يمس الترحيلات (migrations) الحالية. أخبرني إن أردت المتابعة بهذا الاتجاه
لاحقاً، يمكن تنفيذه بحذر دون فقدان أي بيانات.

### بعد رفع هذا التحديث
لا حاجة لأي `migrate` (Jazzmin لا يضيف جداول جديدة). فقط تأكد أن
`collectstatic` نجح (أو أن `WHITENOISE_USE_FINDERS=True` يعمل كما هو
مُفعَّل بالفعل) ليظهر شعار اللوحة وملف CSS المخصص بشكل صحيح.
