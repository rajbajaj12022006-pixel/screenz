"""
Bulk fetch streaming platform availability from JustWatch.
Run: python scripts/fetch_platforms_bulk.py 100
"""
import os
import sys
import time
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'screenz.settings')
django.setup()

from apps.movies.models import Movie
from apps.movies.justwatch_service import sync_platforms_for_movie


def fetch_bulk(limit=100):
    movies = Movie.objects.filter(
        platforms_checked=False
    ).order_by('-popularity')[:limit]

    total = movies.count()
    success = 0
    with_platforms = 0

    print('')
    print('Fetching platforms for {} movies from JustWatch'.format(total))
    print('')

    for i, movie in enumerate(movies, 1):
        print('{}/{}  {}  '.format(i, total, movie.title[:40]), end='', flush=True)

        try:
            platforms = sync_platforms_for_movie(movie)
            if platforms:
                names = ', '.join(p['name'] for p in platforms)
                print('OK {}'.format(names[:60]))
                with_platforms += 1
            else:
                print('- not on major platforms')
            success += 1
        except Exception as e:
            print('ERR {}'.format(e))

        time.sleep(1)

    print('')
    print('Done!')
    print('Checked : {}'.format(success))
    print('Tagged  : {}'.format(with_platforms))


if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    fetch_bulk(limit)
