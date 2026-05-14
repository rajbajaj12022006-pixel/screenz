from django.core.management.base import BaseCommand
from movies.models import Platform


class Command(BaseCommand):
    help = 'Seed streaming platforms into the database'

    def handle(self, *args, **options):
        platforms = [
            {'slug': 'netflix',  'name': 'Netflix',              'color': '#E50914', 'logo_text': 'N'},
            {'slug': 'prime',    'name': 'Amazon Prime Video',   'color': '#00A8E1', 'logo_text': 'P'},
            {'slug': 'jio',      'name': 'JioCinema',            'color': '#4B99D0', 'logo_text': 'J'},
            {'slug': 'hotstar',  'name': 'Disney+ Hotstar',      'color': '#1A67FF', 'logo_text': 'H'},
            {'slug': 'apple',    'name': 'Apple TV+',            'color': '#555555', 'logo_text': 'A'},
            {'slug': 'zee5',     'name': 'ZEE5',                 'color': '#7B2D8B', 'logo_text': 'Z'},
            {'slug': 'sonyliv',  'name': 'SonyLIV',              'color': '#002EFF', 'logo_text': 'S'},
        ]
        for p in platforms:
            obj, created = Platform.objects.update_or_create(
                slug=p['slug'],
                defaults={'name': p['name'], 'color': p['color'], 'logo_text': p['logo_text']}
            )
            status = '✅ Created' if created else '🔄 Updated'
            self.stdout.write(f"{status}: {obj.name}")

        self.stdout.write(self.style.SUCCESS('\nAll platforms seeded!'))
