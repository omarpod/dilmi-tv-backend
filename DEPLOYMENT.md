# خارطة طريق النشر — Railway (الحالي) وVPS عبر Docker (القادم)

المشروع يعمل الآن بأربع "عمليات" منطقية مستقلة، يجب أن تعمل الأربعة معاً
دائماً بغض النظر عن مكان الاستضافة:

| العملية | الأمر | الدور |
|---|---|---|
| `web` | `gunicorn config.wsgi:application` | يخدم الـ API ولوحة التحكم |
| `worker` | `celery -A config worker` | يُنفّذ مهام المزامنة وفحص الروابط |
| `beat` | `celery -A config beat` | يُجدول تلك المهام دورياً (لا تُوسِّعه أبداً — نسخة واحدة فقط) |
| — | Redis + PostgreSQL | يحتاجهما `web`/`worker`/`beat` الثلاثة |

## المسار 1: Railway (الوضع الحالي)

1. **أضف قاعدة بيانات Redis**: من لوحة Railway → New → Database → Redis.
   يُنشئ Railway تلقائياً متغيّر `REDIS_URL` ويُشاركه مع كل خدمات نفس
   المشروع (بنفس آلية `DATABASE_URL` الحالية).
2. **خدمة `worker` جديدة**: New Service → نفس المستودع/الفرع →
   Settings → Deploy → Custom Start Command:
   ```
   celery -A config worker --loglevel=info
   ```
3. **خدمة `beat` جديدة**: نفس الخطوات، لكن الأمر:
   ```
   celery -A config beat --loglevel=info
   ```
4. لكلا الخدمتين: انسخ متغيرات البيئة نفسها من خدمة `web` (خصوصاً
   `RAPIDAPI_KEY`، `NEWS_RSS_FEED_URLS`، `FIREBASE_SERVICE_ACCOUNT_JSON`) —
   `DATABASE_URL` وَ`REDIS_URL` يُشارَكان تلقائياً لأنهما ضمن نفس المشروع.
5. **Build Command** لكلتا الخدمتين: `pip install -r requirements.txt`
   فقط — بدون `collectstatic`/`migrate` (خدمة `web` هي المسؤولة عن ذلك).
6. أمر `run_sync_loop` القديم (حلقة `while True` يدوية) أُزيل نهائياً —
   `beat` + `worker` يحلّان محله بالكامل، بلا أي تغيير في منطق `sync_data`
   نفسه.

## المسار 2: VPS عبر docker-compose (عند الانتقال)

```bash
git clone <repo> && cd dilmi-tv-backend
cp .env.example .env   # املأ القيم الحقيقية (SECRET_KEY، RAPIDAPI_KEY، ...)
docker compose up -d --build
```

هذا يُشغّل `postgres` + `redis` + `web` + `worker` + `beat` كحاويات
منفصلة، بفحوصات صحة (healthcheck) تضمن عدم بدء `web`/`worker`/`beat`
قبل جاهزية `postgres`/`redis` فعلياً.

**التوسّع الأفقي** عند الحاجة لطاقة معالجة أكبر:
```bash
docker compose up -d --scale worker=3
```
عمّال Celery متعددون يستهلكون تلقائياً من نفس طابور Redis دون أي إعداد
إضافي. خدمة `web` نفسها قابلة للتوسيع بنفس الطريقة خلف موازن حمل
(Nginx/Traefik) عند الحاجة — غير مُضافة هنا افتراضياً لتبسيط الإعداد
الأول.

**النسخ الاحتياطي**: بيانات PostgreSQL وRedis محفوظة في named volumes
(`postgres_data`، `redis_data`) — تُنسخ احتياطياً بـ
`docker compose exec postgres pg_dump ...` كالمعتاد مع أي PostgreSQL.
