#!/usr/bin/env python
"""
manage.py
---------
هذا الملف هو نقطة الدخول لإدارة المشروع من سطر الأوامر.
تستخدمه لتشغيل الخادم، أو إنشاء قاعدة البيانات، أو إنشاء مستخدم إداري، إلخ.

أهم الأوامر التي ستحتاجها:
    python manage.py migrate          -> لإنشاء جداول قاعدة البيانات
    python manage.py createsuperuser  -> لإنشاء حساب المدير (لدخول لوحة التحكم)
    python manage.py runserver        -> لتشغيل الخادم محلياً للتجربة
"""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dilmi_tv_backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "تعذر استيراد Django. تأكد من تثبيته عبر: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
