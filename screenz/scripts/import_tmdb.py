"""
TMDB 930K Movies Importer
Dataset: kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies
File: data/TMDB_movie_dataset_v11.csv
Run:
  python scripts/import_tmdb.py          (all 930K movies)
  python scripts/import_tmdb.py 1000     (test with 1000 first)
"""
import os
import sys
import django
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'screenz.settings')
django.setup()

from apps.movies.models import Movie, Genre, Platform
from django.utils.text import slugify

# ── Config ────────────────────────────────────────────────────────
CSV_FILE   = 'data/TMDB_movie_dataset_v11.csv'
BATCH_SIZE = 500

# ── Helpers ───────────────────────────────────────────────────────
def safe_float(val, default=0.0):
    try:
        return float(val or default)
    except Exception:
        return default

def safe_int(val, default=None):
    try:
        v = float(val or 0)
        return int(v) if v > 0 else default
    except Exception:
        return default

def parse_genres(genres_str):
    """
    This dataset stores genres as plain comma-separated text like:
    'Action, Adventure, Science Fiction'
    """
    if not genres_str or genres_str.strip() == '':
        return []
    # Remove brackets if present
    genres_str = genres_str.strip().strip('[]').strip('"').strip("'")
    # Split by comma
    genres = [g.strip().strip('"').strip("'") for g in genres_str.split(',')]
    return [g for g in genres if g and len(g) > 1]

def get_or_create_genre(name):
    name = name.strip()[:100]
    slug = slugify(name)[:50]
    if not slug:
        return None
    genre, _ = Genre.objects.get_or_create(
        name=name,
        defaults={'slug': slug}
    )
    return genre

def seed_platforms():
    platforms = [
        ('Netflix',           'netflix'),
        ('Amazon Prime Video','prime'),
        ('JioCinema',         'jio'),
        ('Disney+ Hotstar',   'hotstar'),
        ('Apple TV+',         'apple'),
        ('ZEE5',              'zee5'),
        ('SonyLIV',           'sonyliv'),
    ]
    for name, slug in platforms:
        Platform.objects.get_or_create(slug=slug, defaults={'name': name})
    print('✅ Platforms ready.')

# ── Main Importer ─────────────────────────────────────────────────
def import_movies(csv_path, limit=None):
    print(f'\n🎬 Starting import from: {csv_path}')
    if limit:
        print(f'   Mode: TEST — importing first {limit} movies')
    else:
        print(f'   Mode: FULL — importing all 930,000 movies')
        print(f'   ⏳ This will take 30-90 minutes. Let it run!\n')

    count   = 0
    skipped = 0
    errors  = 0

    with open(csv_path, encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)

        for row in reader:
            if limit and count >= limit:
                break

            try:
                # ── ID ──────────────────────────────────────────
                tmdb_id = str(row.get('id', '')).strip()
                if not tmdb_id or not tmdb_id.isdigit():
                    skipped += 1
                    continue
                tmdb_id = int(tmdb_id)

                # ── Title ────────────────────────────────────────
                title = (row.get('title') or '').strip()
                if not title:
                    skipped += 1
                    continue

                # ── Release Date ─────────────────────────────────
                release_date = None
                release_year = None
                date_str = (row.get('release_date') or '').strip()
                if date_str:
                    try:
                        release_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                        release_year = release_date.year
                    except Exception:
                        try:
                            release_year = int(date_str[:4])
                        except Exception:
                            pass

                # ── Status → Movie or TV ─────────────────────────
                status_val   = (row.get('status') or '').strip()
                content_type = 'movie'  # this dataset is all movies

                # ── Build movie dict ─────────────────────────────
                movie_data = {
                    'title':             title[:500],
                    'original_title':    (row.get('original_title') or '')[:500],
                    'overview':          (row.get('overview') or '')[:5000],
                    'tagline':           (row.get('tagline') or '')[:500],
                    'content_type':      content_type,
                    'release_date':      release_date,
                    'release_year':      release_year,
                    'vote_average':      safe_float(row.get('vote_average')),
                    'vote_count':        safe_int(row.get('vote_count'), 0),
                    'popularity':        safe_float(row.get('popularity')),
                    'poster_path':       (row.get('poster_path') or '').strip(),
                    'backdrop_path':     (row.get('backdrop_path') or '').strip(),
                    'original_language': (row.get('original_language') or '')[:10],
                    'runtime':           safe_int(row.get('runtime')),
                    'budget':            safe_int(row.get('budget')),
                    'revenue':           safe_int(row.get('revenue')),
                    'status':            status_val[:50],
                    'adult':             str(row.get('adult', 'False')).strip().lower() in ('true', '1'),
                }

                # ── Save to MySQL ────────────────────────────────
                movie, created = Movie.objects.update_or_create(
                    tmdb_id=tmdb_id,
                    defaults=movie_data
                )

                # ── Genres ───────────────────────────────────────
                genres_str = row.get('genres', '')
                if genres_str:
                    for genre_name in parse_genres(genres_str):
                        g = get_or_create_genre(genre_name)
                        if g:
                            movie.genres.add(g)

                count += 1

                # ── Progress update every 500 movies ─────────────
                if count % BATCH_SIZE == 0:
                    print(f'  ✅  {count:,} movies imported  |  skipped: {skipped:,}')

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f'  ⚠️  Error on row: {e}')
                continue

    print(f'\n🎉 Import finished!')
    print(f'   ✅  Movies imported  : {count:,}')
    print(f'   ⏭️  Skipped (no data): {skipped:,}')
    print(f'   ❌  Errors          : {errors:,}')

# ── Run ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    seed_platforms()

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    if not os.path.exists(CSV_FILE):
        print(f'\n❌ File not found: {CSV_FILE}')
        print('   Please place TMDB_movie_dataset_v11.csv inside your data/ folder')
        print('   Download from: kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies')
        sys.exit(1)

    import_movies(CSV_FILE, limit)