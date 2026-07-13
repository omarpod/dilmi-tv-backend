"""
check_db_health.py
--------------------
يتصل مباشرة بقاعدة بيانات Neon الحقيقية ويقارن **الأعمدة الموجودة
فعلياً** في كل جدول مع **الحقول التي يتوقعها Django من models.py** —
هذا يكشف بدقة مطلقة إن كان سبب خطأ 500 هو "عمود/جدول مفقود" (مشكلة
ترحيل/Migration) أو شيء آخر تماماً، دون أي تخمين.

الاستخدام:
    python manage.py check_db_health

يعمل هذا الأمر حتى لو كانت صفحة /admin/ نفسها منهارة تماماً، لأنه يتصل
بقاعدة البيانات مباشرة عبر Django ORM's introspection، بمعزل كامل عن
أي كود عرض (views/admin).
"""
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'يفحص تطابق مخطط قاعدة بيانات Neon الفعلي مع نماذج Django، ويكشف أي عمود/جدول مفقود.'

    def handle(self, *args, **options):
        self.stdout.write('=== فحص الاتصال بقاعدة البيانات ===')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            self.stdout.write(self.style.SUCCESS('الاتصال بقاعدة البيانات ناجح. ✓'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'فشل الاتصال بقاعدة البيانات كلياً: {e}'))
            self.stdout.write(self.style.ERROR(
                'إذا فشل هذا الاتصال، فالمشكلة في DATABASE_URL نفسه '
                '(رابط خاطئ، Neon متوقف مؤقتاً...) وليست في الترحيلات.'
            ))
            return

        self.stdout.write('')
        self.stdout.write('=== مقارنة الجداول والأعمدة الفعلية بما يتوقعه Django ===')

        existing_tables = set(connection.introspection.table_names())
        any_problem_found = False

        for model in apps.get_app_config('core').get_models():
            table_name = model._meta.db_table

            if table_name not in existing_tables:
                any_problem_found = True
                self.stdout.write(self.style.ERROR(
                    f'❌ جدول "{table_name}" (نموذج {model.__name__}) '
                    f'غير موجود إطلاقاً في قاعدة البيانات!'
                ))
                self.stdout.write(self.style.ERROR(
                    '   السبب شبه المؤكد: لم يُشغَّل "makemigrations" بعد '
                    'إضافة هذا النموذج، أو ملف الترحيل لم يُرفَع لـ GitHub.'
                ))
                continue

            # نجلب الأعمدة الفعلية الموجودة في الجدول من قاعدة البيانات نفسها
            with connection.cursor() as cursor:
                actual_columns = {
                    col.name for col in connection.introspection.get_table_description(cursor, table_name)
                }

            # الحقول التي يتوقعها Django من models.py (عمود واحد لكل حقل عادي،
            # وعمود "xxx_id" لكل ForeignKey)
            expected_columns = set()
            for field in model._meta.get_fields():
                if hasattr(field, 'column'):
                    expected_columns.add(field.column)

            missing_columns = expected_columns - actual_columns

            if missing_columns:
                any_problem_found = True
                self.stdout.write(self.style.ERROR(
                    f'❌ جدول "{table_name}" (نموذج {model.__name__}): '
                    f'أعمدة متوقَّعة من models.py لكنها غير موجودة فعلياً في قاعدة البيانات:'
                ))
                for col in sorted(missing_columns):
                    self.stdout.write(self.style.ERROR(f'     - {col}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ جدول "{table_name}" ({model.__name__}) متطابق تماماً.'))

        self.stdout.write('')
        if any_problem_found:
            self.stdout.write(self.style.ERROR(
                '=== الخلاصة: يوجد تعارض حقيقي بين models.py وقاعدة بيانات Neon ==='
            ))
            self.stdout.write(self.style.WARNING(
                'الحل: نفّذ محلياً (بعد ضبط DATABASE_URL لنفس Neon):\n'
                '    python manage.py makemigrations core\n'
                '    python manage.py migrate\n'
                'ثم ارفع مجلد core/migrations/ (الملفات الجديدة بداخله) لـ GitHub، وأعد النشر.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '=== كل الجداول والأعمدة متطابقة تماماً — لا مشكلة في المخطط نفسه ==='
            ))
            self.stdout.write('إذا استمر خطأ 500 رغم هذا، فالسبب في مكان آخر (منطق العرض، لا المخطط).')
