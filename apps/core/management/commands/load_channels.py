"""
apps/core/management/commands/load_channels.py
--------------------------------------------------
تحميل دفعي لقنوات وروابط بثها من ملف JSON — بديل عن الإدخال اليدوي
المتكرر عبر /admin/ عند إضافة عدد كبير من القنوات دفعة واحدة. Django ORM
بالكامل (بدون أي SQL خام) — الحقول الإجبارية (category، معرّف UUID،
created_at/updated_at...) تُضبط تلقائياً بنفس الطريقة التي يضبطها بها
/admin/ نفسه، فلا حاجة لاكتشاف كل عمود إجباري يدوياً.

صيغة ملف JSON المتوقعة:
[
  {
    "name": "اسم القناة",
    "category": "sports",      // اختياري (sports/news/general) — افتراضياً sports
    "is_active": true,          // اختياري — افتراضياً true
    "sources": [
      {"url": "https://...", "label": "HD", "priority": 0},
      {"url": "https://...", "label": "احتياطي", "priority": 1}
    ]
  }
]

الاستخدام:
    python manage.py load_channels path/to/channels.json
    python manage.py load_channels path/to/channels.json --dry-run

آمن لإعادة التشغيل (Idempotent): يبحث عن القناة بالاسم (get_or_create)،
وعن رابط البث بالرابط نفسه ضمن نفس القناة (update_or_create) — تشغيله
مرتين بنفس الملف لن يُنشئ نسخاً مكررة، فقط يُحدّث القيم إن تغيّرت.
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import Channel
from apps.streaming.models import StreamSource

VALID_CATEGORIES = {choice[0] for choice in Channel.Category.choices}


class Command(BaseCommand):
    help = 'يحمّل قنوات وروابط بثها دفعة واحدة من ملف JSON، عبر Django ORM بالكامل.'

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str, help='مسار ملف JSON.')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='يعرض ملخّص ما كان سيُنفَّذ دون تعديل قاعدة البيانات فعلياً.',
        )

    def handle(self, *args, **options):
        json_path = options['json_path']
        dry_run = options['dry_run']

        try:
            with open(json_path, encoding='utf-8') as f:
                raw_channels = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'الملف غير موجود: {json_path}')
        except json.JSONDecodeError as e:
            raise CommandError(f'ملف JSON غير صالح: {e}')

        if not isinstance(raw_channels, list):
            raise CommandError('الملف يجب أن يحتوي قائمة (JSON array) من القنوات.')

        channels_created = channels_updated = 0
        sources_created = sources_updated = 0

        with transaction.atomic():
            for index, entry in enumerate(raw_channels):
                name = (entry.get('name') or '').strip()
                if not name:
                    self.stdout.write(self.style.WARNING(f'[{index}] تم تجاهله — بدون اسم قناة.'))
                    continue

                category = entry.get('category', Channel.Category.SPORTS)
                if category not in VALID_CATEGORIES:
                    raise CommandError(
                        f'[{index}] "{name}": تصنيف غير صالح "{category}" — '
                        f'القيم المسموحة: {sorted(VALID_CATEGORIES)}'
                    )

                channel, created = Channel.objects.get_or_create(
                    name=name,
                    defaults={
                        'category': category,
                        'is_active': entry.get('is_active', True),
                    },
                )
                if created:
                    channels_created += 1
                else:
                    channel.category = category
                    channel.is_active = entry.get('is_active', channel.is_active)
                    channel.save(update_fields=['category', 'is_active'])
                    channels_updated += 1

                for source in entry.get('sources', []):
                    url = (source.get('url') or '').strip()
                    if not url:
                        self.stdout.write(self.style.WARNING(f'[{index}] "{name}": رابط بث بلا url، تم تجاهله.'))
                        continue

                    _, source_created = StreamSource.objects.update_or_create(
                        channel=channel, url=url,
                        defaults={
                            'label': source.get('label', ''),
                            'priority': source.get('priority', 0),
                            'is_active': source.get('is_active', True),
                        },
                    )
                    if source_created:
                        sources_created += 1
                    else:
                        sources_updated += 1

            if dry_run:
                transaction.set_rollback(True)

        summary = (
            f'قنوات جديدة: {channels_created} — قنوات محدَّثة: {channels_updated} — '
            f'روابط بث جديدة: {sources_created} — روابط بث محدَّثة: {sources_updated}'
        )
        if dry_run:
            self.stdout.write(self.style.WARNING(f'[Dry Run — لم يُحفَظ شيء فعلياً] {summary}'))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
