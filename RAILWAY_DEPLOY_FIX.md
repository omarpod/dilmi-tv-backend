# حل مشاكل النشر على Railway — Dilmi TV Backend

بعد الانتقال من Render إلى Railway، `settings.py` نفسه سليم تماماً (نفس
الحل الذي نجح على Render)؛ المشكلة هذه المرة في **كيفية تفسير Railway
لأمر التشغيل**، وليست في كود Django.

## 1. تحقّق مباشر أولاً (30 ثانية) — افعل هذا قبل أي شيء آخر

افتح هذا الرابط مباشرة في متصفحك:
```
https://web-production-d72c6.up.railway.app/static/admin/css/base.css
```

- **404** → الملفات الثابتة غير مُخدَّمة إطلاقاً. تابع الخطوات أدناه.
- **يظهر محتوى CSS فعلي** → المشكلة ليست في الخادم، أخبرني بالتفاصيل
  (قد تكون رابطاً معطوباً في القالب أو ذاكرة تخزين مؤقت في متصفحك).

## 2. السبب الأرجح: Railway يُخمّن أمر تشغيل خاطئ (Nixpacks)

Railway تستخدم أداة **Nixpacks** لاكتشاف نوع المشروع وتخمين أمر التشغيل
تلقائياً. أحياناً تُخمّن تشغيل خادم التطوير (`runserver`) بدل `gunicorn`
الحقيقي، أو لا تُنفّذ `collectstatic` أثناء البناء، خصوصاً إذا لم تُحدّد
هذه الأوامر **صراحة** في المشروع.

### الحل: أضفنا ملف `railway.json` يفرض الأوامر الصحيحة قطعياً

```json
{
  "build": {
    "buildCommand": "pip install -r requirements.txt && python manage.py collectstatic --noinput"
  },
  "deploy": {
    "startCommand": "gunicorn dilmi_tv_backend.wsgi:application --bind 0.0.0.0:$PORT"
  }
}
```

Railway يقرأ هذا الملف تلقائياً من جذر المستودع ويُعطيه أولوية على أي
تخمين تلقائي. لاحظ إضافة `--bind 0.0.0.0:$PORT` صراحة — Railway (خلافاً
لـ Render) يتطلب قراءة متغير البيئة `$PORT` الذي يُحدده هو نفسه، وليس
منفذاً ثابتاً افتراضياً.

## 3. تحقّق يدوياً من إعدادات Railway نفسها (مهم جداً)

حتى مع وجود `railway.json`، تأكد يدوياً من لوحة تحكم Railway:

1. افتح خدمتك ← **Settings** ← تبويب **Deploy**
2. ابحث عن حقل **"Custom Start Command"** — إذا كان يحتوي قيمة يدوية
   موجودة مسبقاً (مثل `python manage.py runserver 0.0.0.0:$PORT`)، فهذه
   القيمة **تتجاوز `railway.json`**! امسحها بالكامل، أو استبدلها يدوياً بـ:
   ```
   gunicorn dilmi_tv_backend.wsgi:application --bind 0.0.0.0:$PORT
   ```
3. تحقق أيضاً من حقل **"Build Command"** بنفس الطريقة.

## 4. أعد النشر

بعد رفع `railway.json` والتحقق من إعدادات لوحة التحكم:
**Deployments ← أعد نشر آخر إصدار (Redeploy)**، أو ادفع أي commit جديد
لتشغيل نشر كامل من جديد.

## 5. تحقّق من سجل البناء (Build Logs)

من تبويب **Deployments** في Railway، افتح آخر عملية نشر وابحث في السجل
عن هذا السطر تحديداً:
```
X static files copied to '/app/staticfiles'
```
- **وجدته** → `collectstatic` نجح فعلاً، والمشكلة في أمر التشغيل فقط
- **لم تجده إطلاقاً** → `collectstatic` لم يُنفَّذ، تأكد أن Build
  Command في `railway.json` أو لوحة التحكم صحيح كما في القسم 2 و 3

## 6. تذكير: `WHITENOISE_USE_FINDERS = True` موجود بالفعل

هذا الإعداد في `settings.py` عندك (صحيح تماماً) يجعل الملفات الثابتة
تُخدَم من مجلداتها الأصلية دون الحاجة لنجاح `collectstatic` إطلاقاً —
لكنه يتطلب أن **الميدلوير نفسه يعمل أصلاً**، أي أن Gunicorn (وليس
`runserver`) هو من يُشغّل التطبيق فعلياً. لهذا التصحيح في القسم 2 و 3
(فرض أمر Gunicorn الصحيح) هو المفتاح الحقيقي لحل المشكلة هذه المرة.
