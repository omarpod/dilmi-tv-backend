# إعادة بناء لوحة التحكم — الاستقرار الكامل

## ⚠️ تصحيح مهم على التشخيص الأصلي

الإصدار الأول من هذا الدليل نسب خطأ `AttributeError: 'super' object
has no attribute 'dicts'` إلى `django-jazzmin`. **هذا التشخيص كان
خاطئاً.** بعد إزالة Jazzmin نهائياً، **ظهر نفس الخطأ بالضبط** داخل
قالب `admin/change_form.html` **الأصلي من Django نفسه** (وليس من أي
مكتبة طرف ثالث) — ما كشف السبب الحقيقي:

**السبب الفعلي: عدم توافق بين Django 5.0.6 وPython 3.14.**
Django 5.0.6 يدعم رسمياً Python 3.10 حتى 3.12 فقط. Render بدأ يستخدم
Python 3.14 تلقائياً (كإصدار افتراضي جديد)، وهذا الإصدار غيّر سلوكاً
داخلياً في طريقة عمل `django/template/context.py` (تحديداً دالة
`__copy__`) بما لا يتوافق مع كود Django 5.0.6 الداخلي — يظهر هذا
تحديداً في صفحات Add/Change لأنها الوحيدة التي تستخدم هذا المسار من
الكود (نسخ الـ Context لمعالجة النماذج المضمّنة/Inline formsets).

**إزالة Jazzmin لم تكن خطأ** (كان يستحق التخلص منه لأسباب استقرار عامة
أخرى)، لكنها لم تكن الحل الحقيقي لهذا الخطأ تحديداً. **الحل الفعلي:
تثبيت إصدار بايثون** الذي يدعمه Django 5.0.6 رسمياً — راجع القسم 1.1.

## 1.1 الحل: تثبيت Python 3.12 صراحة (بدل الافتراضي 3.14 على Render)

أضفنا ملف `runtime.txt` في جذر المشروع:
```
python-3.12.7
```
Render يقرأ هذا الملف تلقائياً لتحديد إصدار بايثون المُستخدَم في البناء.

**⚠️ خطوة يدوية إضافية إلزامية**: بما أن خدمتك موجودة مسبقاً (لم تُنشأ
عبر Render Blueprint من `render.yaml`)، **يجب أيضاً** ضبط متغير البيئة
يدوياً من لوحة التحكم:
```
Render ← خدمتك ← Environment ← أضف متغيراً جديداً:
PYTHON_VERSION = 3.12.7
```
ثم **Manual Deploy → Clear build cache & deploy**. تحقق من سجل البناء
أن أول الأسطر تذكر `Python 3.12.7` وليس `3.14`.

## 2. الملفات التي تغيّرت (من الإصدار الأول لهذا التحديث)

| الملف | التغيير |
|---|---|
| `requirements.txt` | حُذفت `django-jazzmin`، أُضيفت `dj-database-url` و `psycopg[binary]` لـ Neon |
| `settings.py` | حُذفت `JAZZMIN_SETTINGS`/`JAZZMIN_UI_TWEAKS`، `DATABASES` أصبحت Neon-aware، `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` ديناميكية من متغيرات بيئة Render |
| `core/apps.py` | يضبط `site_header`/`site_title` عبر خصائص `AdminSite` الرسمية بدل أي مكتبة |
| `templates/admin/base_site.html` | **جديد** — نقطة التمديد الرسمية لتخصيص الشعار وربط CSS (راجع القسم 3) |
| `core/static/admin/css/admin_custom.css` | **جديد** — ثيم كامل عبر متغيرات CSS الرسمية لـ Django 5 |
| `templates/admin/dilmi_dashboard.html` | أزلنا الاعتماد على أيقونات FontAwesome (كانت تأتي مجاناً مع Jazzmin)، استبدلناها برموز Unicode بسيطة |
| `core/management/commands/create_admin.py` | **جديد** — أمر آمن لإنشاء المدير (راجع القسم 5) |
| `render.yaml` | أضاف `migrate` و `create_admin` لـ Build Command (آمن الآن مع قاعدة بيانات دائمة) |

## 2.3 (تحديث لاحق) `FileNotFoundError` أثناء `collectstatic` نفسه

بعد إضافة Cloudinary، ظهر خطأ بناء جديد:
```
FileNotFoundError: .../staticfiles/admin/img/icon-hidelink.svg
```
هذا حدث أثناء خطوة **ضغط الملفات (gzip)** التي كانت تقوم بها
`CompressedStaticFilesStorage` تلقائياً ضمن `collectstatic` — وهي خطوة
"تحسين أداء" إضافية غير ضرورية لحجم هذا المشروع.

**القرار النهائي:** التحول لـ `django.contrib.staticfiles.storage.StaticFilesStorage`
البسيطة (بدون Manifest، بدون ضغط، بدون أي معالجة إضافية بعد النسخ).
هذا يُزيل نهائياً أي احتمال لفشل `collectstatic` بسبب ملف مرجعي واحد،
دون أي خسارة عملية — لأن `WHITENOISE_USE_FINDERS=True` يخدم الملفات
مباشرة من مجلداتها الأصلية زمن التشغيل أصلاً، بمعزل تام عن نتاج
`collectstatic`.

## 3. كيف نبني "Admin احترافي" دون الوقوع في نفس الأخطاء (دليل عام)

هذا المبدأ ينطبق على أي تخصيص مستقبلي للوحة التحكم:

### ✅ آمن دائماً (نقاط تمديد رسمية موثَّقة من Django نفسه)
- `templates/admin/base_site.html` — الشعار، العنوان، ربط CSS/JS إضافي
  (`{% block branding %}`, `{% block extrastyle %}`, `{% block extrahead %}`)
- `AdminSite.site_header` / `site_title` / `index_title` — عبر بايثون مباشرة
- متغيرات CSS الرسمية لثيم Django 5 (`--primary`, `--header-bg`, إلخ)
- `ModelAdmin.list_display` / `list_filter` / إلخ — كل تخصيصات `admin.py` القياسية

### ⚠️ يتطلب حذراً شديداً
- تمديد `admin/index.html` مباشرة باسم مطابق (خطر "المد الذاتي" —
  الحل: سمِّ ملفك باسم مختلف واربطه عبر `admin.site.index_template`)
- أي مكتبة طرف ثالث تُعيد كتابة قوالب `change_form`/`changelist` بالكامل
  (هذا بالضبط ما فعله Jazzmin وسبَّب العطل) — إن أردت مكتبة مستقبلاً،
  تحقق أولاً من إصدار Django المدعوم رسمياً في توثيقها

### ❌ تجنّبه دائماً
- تعديل ملفات Django الأصلية نفسها مباشرة (داخل `site-packages`)
- الاعتماد على خصائص داخلية غير موثَّقة لأي إصدار Django (`context.dicts` وأمثالها)

## 4. قاعدة البيانات: Neon (PostgreSQL) بدل SQLite

`DATABASES` الآن تقرأ `DATABASE_URL` تلقائياً عبر `dj_database_url`:
- **على Render**: اضبط متغير البيئة `DATABASE_URL` برابط اتصال Neon
  (تحصل عليه من لوحة تحكم Neon مباشرة، بصيغة `postgres://user:pass@host/db`)
- **محلياً على جهازك** (بدون هذا المتغير): يستخدم SQLite تلقائياً كبديل،
  فيستمر التطوير المحلي بلا أي إعداد إضافي

**فرق جوهري عن الإعداد السابق**: بما أن Neon قاعدة بيانات **دائمة**
(خلافاً لملف SQLite المؤقت الذي كان يُعاد إنشاؤه من الصفر كل نشر)، أصبح
تشغيل `python manage.py migrate` ضمن **Build Command نفسه** آمناً
ومنطقياً الآن (راجع `render.yaml`) — لا حاجة بعد الآن لرفع `db.sqlite3`
جاهزاً يدوياً كما كنا نفعل سابقاً.

## 4.1 خطأ 500 عند تسجيل الدخول تحديداً (يظهر بعد الانتقال لـ Neon)

إذا كانت صفحة الدخول تظهر بشكل صحيح (قراءة عادية)، لكن الضغط على
"تسجيل دخول" يعطي `Server Error (500)` (كتابة لقاعدة البيانات: إنشاء
جلسة)، فالسبب شبه مؤكد: **رابط اتصال Neon المُستخدَم هو النسخة "المُجمَّعة"
(Pooled) عبر PgBouncer**، وهي **لا تتوافق** مع الاتصالات الدائمة
(`CONN_MAX_AGE > 0`) التي يفتحها Django افتراضياً.

**الحل المُطبَّق في هذا التحديث:** غيّرنا `conn_max_age` من `600` إلى
**`0`** في `settings.py` — هذا يفتح اتصالاً جديداً نظيفاً لكل طلب بدل
إعادة استخدام اتصال قديم، وهو الإعداد الآمن الموصى به مع أي رابط Neon
مُجمَّع.

**خطوة إضافية اختيارية (أفضل أداء لاحقاً):** من لوحة تحكم Neon، تحقق من
وجود نسختين من رابط الاتصال: **Pooled connection** و **Direct connection**.
إذا استخدمت رابط **Direct** بدل Pooled في `DATABASE_URL`، يمكنك إعادة
`conn_max_age` إلى قيمة أعلى (مثل 60) بأمان لتحسين الأداء، لأن الاتصال
المباشر يدعم الاتصالات الدائمة بشكل طبيعي.

## 5. أمر `create_admin` — لماذا هو آمن ولا يتعارض مع الـ Build

`python manage.py createsuperuser` الجاهز من Django **تفاعلي** (يطلب
كتابة اسم مستخدم وكلمة مرور يدوياً)، وهذا **يُفشل** أي عملية بناء آلية
غير تفاعلية (مثل Build على Render). أمرنا المخصص `create_admin`:

1. يقرأ كل البيانات من متغيرات بيئة (`DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD`)
2. **Idempotent**: إذا كان المستخدم موجوداً، لا يفعل شيئاً ولا يفشل —
   آمن لتشغيله في **كل** عملية بناء دون أي خطر تكرار
3. لا يحتوي أي كلمة مرور مكتوبة في الكود نفسه

### اضبط هذه المتغيرات من Render ← Environment
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=كلمة-مرور-قوية-هنا
```

## 6. تضارب اللغات (عربي/إنجليزي)

كان مصدره الوحيد: نصوص Jazzmin الإنجليزية الثابتة (`welcome_sign`,
`site_brand`...) تظهر بجانب ترجمة Django العربية الرسمية لباقي اللوحة.
بعد إزالة Jazzmin، اللوحة بأكملها تستخدم **ترجمة Django الرسمية للعربية**
(`LANGUAGE_CODE = 'ar'`) بشكل متسق 100%، وكل النصوص المخصصة التي أضفناها
(العنوان، بطاقات الإحصائيات) بالعربية فقط.

## 7. متغيرات البيئة المطلوبة على Render (الخلاصة الكاملة)

```
SECRET_KEY=مفتاح-سري-عشوائي-طويل
DATABASE_URL=(رابط Neon الكامل)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=كلمة-مرور-قوية
```
`RENDER_EXTERNAL_HOSTNAME` يُضبط تلقائياً من Render نفسه — لا حاجة لأي
تدخل يدوي منك.

## 8. خطوات النشر الكاملة (من الصفر)

```bash
git add -A
git commit -m "إعادة هيكلة كاملة: إزالة Jazzmin، الانتقال لـ Neon"
git push
```
ثم من Render:
1. اضبط متغيرات البيئة في القسم 7 أعلاه
2. **Manual Deploy → Clear build cache & deploy**
3. راقب سجل البناء للتأكد من ظهور: `تم إنشاء حساب المدير "admin" بنجاح.`
