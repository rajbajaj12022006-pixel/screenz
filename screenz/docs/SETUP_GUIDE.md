# Screenz – Complete Setup Guide (Windows)

## Step 1: Install Task Master
```bash
npm install -g task-master-ai
task-master list     # See all 12 tasks
task-master next     # What to do next
task-master done T01 # Mark task complete
```

## Step 2: Python Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3: MySQL Database
```sql
CREATE DATABASE screenz_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Then update `screenz/settings.py` → DATABASES with your MySQL username/password.

## Step 4: Run Migrations
```bash
python manage.py makemigrations accounts
python manage.py makemigrations movies
python manage.py makemigrations watchlist
python manage.py migrate
python manage.py createsuperuser
```

## Step 5: Download TMDB Dataset
- https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata  (5K movies, quick)
- https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset  (1M movies)

Place CSV at: `data/tmdb_movies.csv`

## Step 6: Import Movies
```bash
python scripts/import_tmdb.py data/tmdb_movies.csv 1000   # test with 1K
python scripts/import_tmdb.py data/tmdb_movies.csv        # full import
```

## Step 7: Run Server
```bash
python manage.py runserver
```
Open: http://127.0.0.1:8000

## Pages
| URL | Page |
|-----|------|
| /accounts/login/ | Login / Sign Up |
| / | Home – trending, new movies |
| /search/ | Search + filters |
| /movie/<id>/ | Movie detail |
| /accounts/profile/ | Profile + watchlist |
| /admin/ | Admin panel |

## Cursor AI Tips
The `.cursor/rules` file already explains the full project to Cursor.
Ask Cursor things like:
- "Add Bollywood filter to search"
- "Make the watchlist page paginated"
- "Add a movie rating system with stars"
