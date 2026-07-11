#!/usr/bin/env python
"""
manage.py - تم تعديله للقيام بعملية migrate تلقائية عند بدء تشغيل الخادم
"""
import os
import sys
from django.core.management import execute_from_command_line, call_command

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dilmi_tv_backend.settings')
    
    # محاولة تشغيل الـ migrate تلقائياً عند البدء لتجنب أخطاء الجداول المفقودة
    if 'runserver' not in sys.argv:
        try:
            print("--- Running automatic migration ---")
            call_command('migrate', '--noinput')
            print("--- Migration completed successfully ---")
        except Exception as e:
            print(f"--- Migration failed: {e} ---")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "تعذر استيراد Django. تأكد من تثبيته عبر: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
