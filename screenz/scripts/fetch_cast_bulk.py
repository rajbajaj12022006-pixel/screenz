"""
Bulk fetch cast and director for all movies from Wikipedia
Run: python scripts/fetch_cast_bulk.py 100
     (fetches cast for top 100 popular movies)
"""
import os
import sys
import django
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'screenz.settings')
django.setup()

from apps.movies.models import Movie
from apps.movies.cast_service import get_cast_and_director

def fetch_bulk(limit=100):
    # Only get movies without cast info
    movies = Movie.objects.filter(
        cast='',
        director=''
    ).order_by('-popularity')[:limit]

    total   = movies.count()
    success = 0
    failed  = 0

    print('')
    print('Fetching cast for {} movies from Wikipedia'.format(total))
    print('Takes about {} minutes'.format(total * 4 // 60 + 1))
    print('')

    for i, movie in enumerate(movies, 1):
        print('{}/{}  {}  '.format(
            i, total, movie.title[:40]
        ), end='', flush=True)

        director, cast = get_cast_and_director(
            movie.title,
            movie.release_year
        )

        if director or cast:
            movie.director = director
            movie.cast     = cast
            movie.save(update_fields=['director', 'cast'])
            print('✅ Dir: {} | Cast: {}...'.format(
                director[:20] if director else 'N/A',
                cast[:30] if cast else 'N/A'
            ))
            success += 1
        else:
            print('❌ not found')
            failed += 1

        # Wait 2 seconds between requests
        time.sleep(2)

    print('')
    print('Done!')
    print('Success : {}'.format(success))
    print('Failed  : {}'.format(failed))

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    fetch_bulk(limit)