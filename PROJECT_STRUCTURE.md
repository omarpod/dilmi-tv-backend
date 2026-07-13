# هيكل مشروع Dilmi TV Backend v2 — Production-Ready

```
dilmi_backend_v2/
│
├── manage.py
├── requirements.txt
├── railway.json                 ← إعدادات Railway (Build/Start Command)
├── Procfile                     ← احتياطي/مرجعي
├── .gitignore
│
├── config/                      ← إعدادات المشروع العامة (بدل اسم المشروع
│   ├── __init__.py                القديم "dilmi_tv_backend" — اسم "config"
│   ├── settings.py                 عام ومحايد، شائع في المشاريع الاحترافية)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                         ← كل تطبيقات Django تحت مجلد واحد منظَّم
│   └── core/                       (بدل تفريقها في جذر المشروع مباشرة)
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py              ← Match, News, Channel (UUID PKs)
│       ├── admin.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── migrations/
│       └── management/
│           └── commands/
│               └── sync_data.py   ← يُشغَّل عبر Railway Cron Job (ليس APScheduler)
│
├── staticfiles/                  ← ناتج collectstatic (لا يُرفع لـ git، مُتجاهَل)
└── media/                        ← ملفات مرفوعة (إن لم تُستخدم Cloudinary)
```

## لماذا هذا الهيكل تحديداً (وليس الهيكل المسطَّح السابق)؟

1. **`config/` بدل `dilmi_tv_backend/`**: اسم محايد لا يتكرر مع اسم أي
   تطبيق فرعي مستقبلي، ويطابق الاصطلاح الشائع في مشاريع Django
   الاحترافية (Cookiecutter Django وغيرها تستخدم نفس النمط).

2. **`apps/` كمجلد حاوٍ**: عندما يكبر المشروع لاحقاً (تطبيقات منفصلة
   لكل من users، matches، news بدل تطبيق core واحد ضخم)، الهيكل جاهز
   لذلك دون إعادة تنظيم لاحقة مُربكة.

3. **فصل `management/commands/sync_data.py`** كنقطة دخول وحيدة ونظيفة
   لكل منطق سحب البيانات — مُصمَّمة خصيصاً لتعمل كـ **Railway Cron Job**
   (تُنفَّذ، تنجز مهمتها، **تخرج (exit) فوراً** — هذا شرط إلزامي من
   Railway نفسه لخدمات الـ Cron، راجع القسم 5 في الرسالة).
