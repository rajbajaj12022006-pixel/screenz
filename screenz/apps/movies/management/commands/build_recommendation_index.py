from django.core.management.base import BaseCommand

from apps.movies.recommendations import build_movie_index


class Command(BaseCommand):
    help = 'Build sklearn movie recommendation index (TF-IDF + genres + numeric features)'

    def handle(self, *args, **options):
        self.stdout.write('Building recommendation index...')
        index = build_movie_index()
        self.stdout.write(self.style.SUCCESS(
            'Index built for {} movies.'.format(len(index.movie_ids))
        ))
