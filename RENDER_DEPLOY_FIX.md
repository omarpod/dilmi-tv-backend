# حل مشاكل النشر على Render (الخطة المجانية) — Dilmi TV Backend

هذا الدليل يحل مشكلتين واجهتهما بالضبط: `Server Error (500)` بسبب جدول
مفقود، وعدم ظهور تنسيق CSS في لوحة `/admin/`.

## 1. المشكلة الأولى: `no such table: core_sitesettings`

**السبب المؤكد:** لم يُنشأ ملف الترحيل (migration) الخاص بالنماذج الأربعة
الجديدة (`Analytics`، `SiteSettings`، `NotificationSubscriber`،
`StaticPage`) بعد إضافتها، ولذلك `db.sqlite3` الذي رفعته لا يحتوي هذه
الجداول فعلياً.

### الحل (نفّذه محلياً على جهازك، وليس على Render)

```bash
cd dilmi_tv_backend
python manage.py makemigrations core
python manage.py migrate
```

تحقق أن الجداول الجديدة أصبحت موجودة فعلاً قبل المتابعة:
```bash
python manage.py shell -c "from django.db import connection; print([t for t in connection.introspection.table_names() if 'core_' in t])"
```
يجب أن تظهر: `core_analytics`، `core_sitesettings`،
`core_notificationsubscriber`، `core_staticpage` ضمن القائمة.

### ثم ارفع الملفين معاً لـ GitHub (كلاهما ضروري، ليس أحدهما فقط)

```bash
git add core/migrations/ db.sqlite3
git commit -m "إضافة ترحيل النماذج الجديدة"
git push
```

⚠️ **تحقق يدوياً على واجهة GitHub نفسها** (ادخل للمستودع في المتصفح) أن:
- مجلد `core/migrations/` يحتوي فعلاً ملفاً جديداً مثل `0002_xxx.py`
- ملف `db.sqlite3` يحمل تاريخ تعديل حديث (اليوم نفسه)

إذا كان ملف الترحيل الجديد **غير موجود على GitHub رغم وجوده عندك محلياً**،
فهذا يعني أن `.gitignore` عندك يستثنيه. افتح `.gitignore` وتأكد أن هذين
النمطين **غير موجودين** فيه (بعض قوالب GitHub الافتراضية لـ Python تضيفهما
تلقائياً):
```
db.sqlite3
migrations/
```
إذا وجدتهما، احذفهما، ثم أعد تنفيذ `git add` و `git commit` و `git push`.

### بعد الرفع

من لوحة Render: **Manual Deploy → Clear build cache & deploy** (وليس
"Deploy latest commit" العادي)، لضمان عدم استخدام أي نسخة قديمة مخزّنة
مؤقتاً من `db.sqlite3` أو الكود.

## 2. المشكلة الثانية: CSS لا يعمل في `/admin/`

**السبب:** وضع أمر `collectstatic` في **Start Command** (يعمل وقت
التشغيل الفعلي، حيث الكتابة مقيّدة/غير مستقرة على الخطة المجانية) بدل
**Build Command** (يعمل مرة واحدة أثناء البناء، حيث الكتابة مسموحة دائماً
على كل خطط Render بما فيها المجانية).

أضفنا **WhiteNoise** (الحل القياسي لخدمة الملفات الثابتة من Django/Gunicorn
مباشرة دون خادم ويب منفصل)، وأضفنا `STATIC_ROOT` و `STORAGES` في
`settings.py`. تبقّى فقط تصحيح إعدادات Render نفسها:

### اذهب للوحة تحكم Render ← خدمتك ← Settings

**Build Command** (استبدله بهذا بالضبط):
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command** (يجب أن يكون هذا فقط، بدون أي أمر آخر):
```bash
gunicorn dilmi_tv_backend.wsgi:application
```

**لا تضع `migrate` ولا `collectstatic` في Start Command إطلاقاً** — نحن
نستخدم `db.sqlite3` جاهزاً مرفوعاً مسبقاً (كما طلبت: "تشغيل المشروع كما
هو دون عمليات كتابة أثناء التشغيل")، فلا حاجة لـ `migrate` وقت التشغيل
مطلقاً، و`collectstatic` انتقل لمرحلة البناء أعلاه.

### احفظ ثم أعد النشر

**Manual Deploy → Clear build cache & deploy**.

## 3. ملاحظات إضافية مهمة

### أ) `DEBUG` قبل النشر النهائي
`settings.py` الحالي فيه `DEBUG = True` (مفيد للتشخيص الآن). بعد التأكد
أن كل شيء يعمل، غيّرها إلى `DEBUG = False` لأي استخدام حقيقي (تسريب
معلومات حساسة في صفحات الخطأ التفصيلية أثناء `DEBUG = True` في الإنتاج
خطر أمني حقيقي).

### ب) الصور المرفوعة عبر `/admin/` (شعارات، صور أخبار...) لن تدوم
بما أنك على الخطة المجانية بدون **Persistent Disk**، أي صورة ترفعها من
`/admin/` بعد النشر (وليست جزءاً من `db.sqlite3` أو الكود المرفوع أصلاً)
**ستُحذف عند أي إعادة نشر أو إعادة تشغيل تلقائي للخادم**. هذا ينطبق على
`MEDIA_ROOT` فقط (الصور)، وليس على `db.sqlite3` نفسه (الذي يبقى لأنه جزء
من الكود المرفوع لـ GitHub، وليس ملفاً كُتب أثناء التشغيل).

إذا احتجت لاحقاً رفع صور فعلية تدوم (شعار قناة جديد مثلاً)، الخيار الأصح
طويل المدى هو خدمة تخزين خارجية دائمة مثل Cloudinary أو AWS S3 — خارج
نطاق هذا الإصلاح الحالي، أخبرني إن احتجتها.

### ج) لماذا لا نستخدم `migrate` على Render أصلاً؟
لأن **خدمات الويب المجانية على Render لا توفر وصول Shell/Console** (ميزة
مدفوعة فقط)، فلا يمكنك تنفيذ أوامر يدوياً على الخادم نفسه بعد النشر. هذا
تحديداً سبب اعتمادنا على رفع `db.sqlite3` جاهزاً من جهازك بدل الاعتماد
على تنفيذ `migrate` على الخادم كما هو معتاد في نشر Django التقليدي.
