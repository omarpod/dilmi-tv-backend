# صورة إنتاج واحدة تُستخدم من كل خدمات docker-compose الأربع (web/worker/
# beat) — كل منها يُشغّل نفس الصورة بأمر تشغيل مختلف فقط (انظر docker-compose.yml)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libpq-dev + gcc مطلوبان لبناء psycopg (عميل PostgreSQL) من المصدر عند
# عدم توفر عجلة (wheel) جاهزة للمعمارية المستهدفة
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
