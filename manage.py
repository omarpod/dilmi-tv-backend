#!/usr/bin/env python
import os
import sys

def main():
    """تشغيل المهام الإدارية."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dilmi_tv_backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "تعذر استيراد Django. تأكد من تثبيته وتفعيله في بيئتك الافتراضية."
        ) from exc
    
    # تنفيذ الأمر الممرر (مثل migrate أو collectstatic)
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
