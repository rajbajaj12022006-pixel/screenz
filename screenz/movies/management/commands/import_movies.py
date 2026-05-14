import csv
import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from movies.models import Movie, Genre


class Command(BaseCommand):
    help = 'Import movies from a TMDB CSV dataset file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to the CSV file')
        parser.add_argument('--limit', type=int, default=None, help='Max number of movies to import')
        parser.add_argument('--skip', type=int, default=0, help='Number of rows to skip')

    def handle(self, *args, **options):
        filepath = options['file']
        limit = options['limit']
        skip = options['skip']

        if not os.path.exists(filepath):
            raise CommandError(f"File not found: {filepath}")

        self.stdout.write(f"Starting import from {filepath}...")
        if limit:
            self.stdout.write(f"Limit: {limit} movies")

        imported = 0
        skipped = 0
        errors = 0
        genres_cache = {}

        def get_or_create_genre(name):
            name = name.strip()
            if name not in genres_cache:
                slug = slugify(name)
                genre, _ = Genre.objects.get_or_create(name=name, defaults={'slug': slug})
                genres_cache[name] = genre
            return genres_cache[name]

        def parse_date(date_str):
            if not date_str or date_str.strip() == '':
                return None
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y'):
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
            return None

        def parse_genres(genres_str):
            if not genres_str or genres_str.strip() == '':
                return []
            try:
                # Try JSON format: [{"id":28,"name":"Action"}, ...]
                genres_data = json.loads(genres_str.replace("'", '"'))
                return [g['name'] for g in genres_data if 'name' in g]
            except (json.JSONDecodeError, TypeError):
                # Try plain comma-separated
                return [g.strip() for g in genres_str.split(',') if g.strip()]

        movies_to_create = []
        movie_genres_map = {}

        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                self.stdout.write(f"Columns found: {fieldnames}")

                # Map common TMDB column name variants
                col_map = {}
                for col in (fieldnames or []):
                    cl = col.lower().strip()
                    if cl in ('id', 'tmdb_id', 'movie_id'):
                        col_map['tmdb_id'] = col
                    elif cl == 'title':
                        col_map['title'] = col
                    elif cl in ('original_title',):
                        col_map['original_title'] = col
                    elif cl in ('overview', 'description'):
                        col_map['overview'] = col
                    elif cl in ('release_date', 'releasedate'):
                        col_map['release_date'] = col
                    elif cl in ('vote_average', 'rating', 'score'):
                        col_map['vote_average'] = col
                    elif cl in ('vote_count',):
                        col_map['vote_count'] = col
                    elif cl in ('popularity',):
                        col_map['popularity'] = col
                    elif cl in ('poster_path', 'poster'):
                        col_map['poster_path'] = col
                    elif cl in ('backdrop_path', 'backdrop'):
                        col_map['backdrop_path'] = col
                    elif cl in ('runtime',):
                        col_map['runtime'] = col
                    elif cl in ('genres', 'genre'):
                        col_map['genres'] = col
                    elif cl in ('budget',):
                        col_map['budget'] = col
                    elif cl in ('revenue',):
                        col_map['revenue'] = col
                    elif cl in ('original_language', 'language'):
                        col_map['original_language'] = col
                    elif cl in ('tagline',):
                        col_map['tagline'] = col

                self.stdout.write(f"Column mapping: {col_map}")

                if 'tmdb_id' not in col_map or 'title' not in col_map:
                    raise CommandError("CSV must have 'id' (tmdb_id) and 'title' columns")

                for i, row in enumerate(reader):
                    if i < skip:
                        continue
                    if limit and (i - skip) >= limit:
                        break

                    try:
                        tmdb_id_raw = row.get(col_map.get('tmdb_id', ''), '').strip()
                        title = row.get(col_map.get('title', ''), '').strip()

                        if not tmdb_id_raw or not title:
                            skipped += 1
                            continue

                        try:
                            tmdb_id = int(float(tmdb_id_raw))
                        except (ValueError, TypeError):
                            skipped += 1
                            continue

                        release_date = parse_date(row.get(col_map.get('release_date', ''), ''))
                        release_year = release_date.year if release_date else None

                        try:
                            vote_average = float(row.get(col_map.get('vote_average', ''), 0) or 0)
                        except (ValueError, TypeError):
                            vote_average = 0.0

                        try:
                            vote_count = int(float(row.get(col_map.get('vote_count', ''), 0) or 0))
                        except (ValueError, TypeError):
                            vote_count = 0

                        try:
                            popularity = float(row.get(col_map.get('popularity', ''), 0) or 0)
                        except (ValueError, TypeError):
                            popularity = 0.0

                        try:
                            runtime = int(float(row.get(col_map.get('runtime', ''), 0) or 0)) or None
                        except (ValueError, TypeError):
                            runtime = None

                        try:
                            budget = int(float(row.get(col_map.get('budget', ''), 0) or 0))
                        except (ValueError, TypeError):
                            budget = 0

                        try:
                            revenue = int(float(row.get(col_map.get('revenue', ''), 0) or 0))
                        except (ValueError, TypeError):
                            revenue = 0

                        genre_names = parse_genres(row.get(col_map.get('genres', ''), ''))

                        movie = Movie(
                            tmdb_id=tmdb_id,
                            title=title,
                            original_title=row.get(col_map.get('original_title', ''), '').strip(),
                            overview=row.get(col_map.get('overview', ''), '').strip(),
                            tagline=row.get(col_map.get('tagline', ''), '').strip(),
                            release_date=release_date,
                            release_year=release_year,
                            vote_average=vote_average,
                            vote_count=vote_count,
                            popularity=popularity,
                            runtime=runtime,
                            budget=budget,
                            revenue=revenue,
                            poster_path=row.get(col_map.get('poster_path', ''), '').strip(),
                            backdrop_path=row.get(col_map.get('backdrop_path', ''), '').strip(),
                            original_language=row.get(col_map.get('original_language', ''), '').strip()[:10],
                        )
                        movies_to_create.append(movie)
                        movie_genres_map[tmdb_id] = genre_names

                    except Exception as e:
                        errors += 1
                        if errors <= 5:
                            self.stdout.write(self.style.WARNING(f"Row {i} error: {e}"))
                        continue

                    # Bulk insert every 1000 rows
                    if len(movies_to_create) >= 1000:
                        created = Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                        imported += len(created)

                        # Assign genres to newly created movies
                        for m in created:
                            genre_names = movie_genres_map.get(m.tmdb_id, [])
                            if genre_names:
                                genre_objs = [get_or_create_genre(g) for g in genre_names]
                                m.genres.set(genre_objs)

                        movies_to_create = []
                        self.stdout.write(f"  Imported {imported} movies so far...")

            # Insert remaining
            if movies_to_create:
                created = Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                imported += len(created)
                for m in created:
                    genre_names = movie_genres_map.get(m.tmdb_id, [])
                    if genre_names:
                        genre_objs = [get_or_create_genre(g) for g in genre_names]
                        m.genres.set(genre_objs)

        except FileNotFoundError:
            raise CommandError(f"File not found: {filepath}")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Import complete!\n"
            f"   Imported: {imported}\n"
            f"   Skipped:  {skipped}\n"
            f"   Errors:   {errors}"
        ))
