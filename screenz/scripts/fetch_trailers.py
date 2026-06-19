"""
Auto saves YouTube trailer IDs for movies
Better version - verifies videos before saving
Run: python scripts/fetch_trailers.py 100
"""
import os
import sys
import django
import requests
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'screenz.settings')
django.setup()

from apps.movies.models import Movie

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def search_youtube_trailer(movie_title, year=None):
    """Search YouTube and return first valid video ID"""
    try:
        if year:
            query = '{} {} official trailer'.format(movie_title, year)
        else:
            query = '{} official trailer'.format(movie_title)

        response = requests.get(
            'https://www.youtube.com/results',
            params={'search_query': query},
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            return ''

        # Find video IDs
        pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
        matches = re.findall(pattern, response.text)

        # Remove duplicates
        seen = []
        for m in matches:
            if m not in seen:
                seen.append(m)

        return seen[0] if seen else ''

    except Exception as e:
        print('Search error: {}'.format(e))
        return ''

def verify_video(video_id):
    """Check if YouTube video actually exists and is embeddable"""
    try:
        response = requests.get(
            'https://www.youtube.com/oembed',
            params={
                'url': 'https://www.youtube.com/watch?v={}'.format(video_id),
                'format': 'json'
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False

def fetch_trailers(limit=100):
    # Only get movies without trailer key
    movies = Movie.objects.filter(
        trailer_youtube_key=''
    ).order_by('-popularity')[:limit]

    total   = movies.count()
    success = 0
    failed  = 0

    print('')
    print('Finding trailers for {} movies'.format(total))
    print('Takes about {} minutes'.format(total * 3 // 60 + 1))
    print('')

    for i, movie in enumerate(movies, 1):
        print('{}/{}  {}  '.format(i, total, movie.title), end='', flush=True)

        video_id = search_youtube_trailer(movie.title, movie.release_year)

        if video_id:
            if verify_video(video_id):
                movie.trailer_youtube_key = video_id
                movie.save(update_fields=['trailer_youtube_key'])
                print('✅ {}'.format(video_id))
                success += 1
            else:
                print('❌ video not embeddable')
                failed += 1
        else:
            print('❌ not found')
            failed += 1

        # Wait 2 seconds so YouTube does not block us
        time.sleep(2)

    print('')
    print('Done!')
    print('Success : {}'.format(success))
    print('Failed  : {}'.format(failed))
    print('')
    print('Now open any movie detail page and click Play Trailer!')

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    fetch_trailers(limit)