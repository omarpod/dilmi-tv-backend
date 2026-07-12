# إعادة بناء لوحة التحكم — الاستقرار الكامل بدون Jazzmin

هذا التحديث يتخلّى نهائياً عن `django-jazzmin` وينتقل لثيم Django 5
**الأصلي** مُخصَّصاً عبر النقاط الرسمية والموثَّقة فقط، لضمان استقرار
تام مع أي تحديث مستقبلي لـ Django أو Python.

## 1. السبب الجذري لعطل `AttributeError: 'super' object has no attribute 'dicts'`

هذا عطل توافق معروف بين `django-jazzmin` وDjango 5: تعتمد قوالب Jazzmin
الداخلية (خصوصاً `admin/change_form.html`) على طريقة قديمة للتعامل مع
كائن `Context` الداخلي في Django (`context.dicts`)، وهي طريقة **تغيّر
سلوكها الداخلي في Django 5** بما لا يتوافق مع افتراضات Jazzmin القديمة.
هذا يفسّر أيضاً لماذا **تعطيل Jazzmin من `INSTALLED_APPS` وحده لا يكفي**:
أي بايت-كود مُصرَّف مؤقتاً (`__pycache__`) أو قوالب مؤقتة على منصة
الاستضافة قد تبقى "متروسِّبة" حتى يُنظَّف كل أثر لها فعلياً.

**الحل الوحيد المضمون: إزالة المكتبة نهائياً** — وهذا ما نفّذناه هنا.

## 2. الملفات التي تغيّرت

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
