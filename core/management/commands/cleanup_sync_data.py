"""
cleanup_sync_data.py
----------------------
يفحص قاعدة البيانات بحثاً عن سجلات "معطوبة" ناتجة عن مزامنة API دفاعية
(مثل League أو Team باسم فارغ، لأن الحقل الحقيقي في استجابة الـ API
كان بصيغة مختلفة عمّا توقعه match_sync.py الحالي).

الاستخدام (آمن دائماً، لا يحذف شيئاً افتراضياً):
    python manage.py cleanup_sync_data          # فحص وعرض فقط (Dry Run)
    python manage.py cleanup_sync_data --apply  # يحذف فعلياً بعد المراجعة

== لماذا "Dry Run" افتراضياً؟ ==
حذف بيانات خطأ لا يمكن التراجع عنه. نعرض لك أولاً **بالضبط** ماذا
سيُحذف، وتقرر أنت بوعي كامل عبر --apply.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import League, Team, Match


class Command(BaseCommand):
    help = 'يفحص وينظّف السجلات المعطوبة الناتجة عن مزامنة API (أسماء فارغة، بيانات ناقصة).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='احذف فعلياً بعد الفحص (بدونها: عرض فقط دون حذف).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']

        self.stdout.write('=== فحص البطولات (League) ===')
        broken_leagues = League.objects.filter(Q(name='') | Q(name__isnull=True))
        self._report_and_maybe_delete(broken_leagues, 'بطولة', apply_changes)

        self.stdout.write('')
        self.stdout.write('=== فحص الفرق (Team) ===')
        broken_teams = Team.objects.filter(Q(name='') | Q(name__isnull=True))
        self._report_and_maybe_delete(broken_teams, 'فريق', apply_changes)

        self.stdout.write('')
        self.stdout.write('=== فحص تكرار external_id (احتمال تصادم بيانات) ===')
        self._report_duplicate_external_ids(League, 'بطولة')
        self._report_duplicate_external_ids(Team, 'فريق')

        self.stdout.write('')
        if apply_changes:
            self.stdout.write(self.style.SUCCESS('تم تنفيذ الحذف أعلاه فعلياً.'))
        else:
            self.stdout.write(self.style.WARNING(
                'هذا كان عرضاً فقط (Dry Run) — لم يُحذف شيء بعد. '
                'أعد التشغيل مع --apply للحذف الفعلي.'
            ))

    def _report_and_maybe_delete(self, queryset, label, apply_changes):
        count = queryset.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'لا توجد سجلات {label} معطوبة. ✓'))
            return

        self.stdout.write(self.style.WARNING(f'وُجد {count} سجل {label} باسم فارغ:'))
        for obj in queryset[:20]:  # نعرض أول 20 فقط تفادياً لإغراق الشاشة
            self.stdout.write(f'  - id={obj.id}, external_id={obj.external_id}')

        if apply_changes:
            deleted_count, _ = queryset.delete()
            self.stdout.write(self.style.SUCCESS(f'تم حذف {deleted_count} سجل {label} معطوب.'))
        else:
            self.stdout.write(f'  (لن يُحذف شيء إلا مع --apply)')

    def _report_duplicate_external_ids(self, model, label):
        from django.db.models import Count

        duplicates = (
            model.objects.exclude(external_id__isnull=True)
            .values('external_id')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        if not duplicates:
            self.stdout.write(self.style.SUCCESS(f'لا يوجد تكرار في external_id لنموذج {label}. ✓'))
            return

        self.stdout.write(self.style.WARNING(f'تحذير: external_id مكرر في {label}:'))
        for dup in duplicates:
            self.stdout.write(f"  - external_id='{dup['external_id']}' مُستخدَم {dup['count']} مرة")
        self.stdout.write(
            '  (هذا لا يجب أن يحدث فعلياً بفضل unique=True في قاعدة البيانات؛ '
            'إن ظهر، أخبرني فوراً فهو مؤشر خطأ أعمق يستحق فحصاً منفصلاً)'
        )
