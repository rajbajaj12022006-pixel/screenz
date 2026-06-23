from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Movie, Genre, Platform
from .recommendations import (
    get_recommendations_for_user,
    get_similar_for_user,
    user_has_history,
)

@login_required
def home_view(request):
    trending   = Movie.objects.filter(vote_average__gte=7.0).order_by('-popularity')[:10]
    new_movies = Movie.objects.filter(content_type='movie').order_by('-added_at')[:10]
    new_shows  = Movie.objects.filter(content_type='tv').order_by('-added_at')[:10]
    genres     = Genre.objects.all()
    platforms  = Platform.objects.all()
    recommendations = get_recommendations_for_user(request.user, limit=12)
    return render(request, 'movies/home.html', {
        'trending':        trending,
        'new_movies':      new_movies,
        'new_shows':       new_shows,
        'genres':          genres,
        'platforms':       platforms,
        'recommendations': recommendations,
    })

@login_required
def search_view(request):
    query             = request.GET.get('q', '').strip()
    selected_type     = request.GET.get('type', '')
    selected_genre    = request.GET.get('genre', '')
    selected_platform = request.GET.get('platform', '')
    selected_year     = request.GET.get('year', '')
    selected_lang     = request.GET.get('lang', '')
    selected_sort     = request.GET.get('sort', '-popularity')

    movies = Movie.objects.all()

    if query:
        movies = movies.filter(
            Q(title__icontains=query) | Q(overview__icontains=query)
        )
    if selected_type in ('movie', 'tv'):
        movies = movies.filter(content_type=selected_type)
    if selected_genre:
        movies = movies.filter(genres__id=selected_genre)
    if selected_platform:
        valid_slugs = set(
            Platform.objects.values_list('slug', flat=True)
        )
        if selected_platform in valid_slugs:
            tagged = Movie.objects.filter(
                platforms__slug=selected_platform
            ).distinct().count()
            if tagged == 0:
                from .justwatch_service import sync_platforms_for_movie
                unchecked = Movie.objects.filter(
                    platforms_checked=False
                ).order_by('-popularity')[:10]
                for movie in unchecked:
                    sync_platforms_for_movie(movie)
            movies = movies.filter(platforms__slug=selected_platform)
    if selected_year:
        movies = movies.filter(release_year=selected_year)
    if selected_lang:
        movies = movies.filter(original_language=selected_lang)

    SORT_OPTIONS = {
        '-popularity':   '-popularity',
        '-vote_average': '-vote_average',
        '-release_year': '-release_year',
        'title':         'title',
    }
    movies = movies.order_by(
        SORT_OPTIONS.get(selected_sort, '-popularity')
    ).distinct()

    paginator = Paginator(movies, 24)
    page_obj  = paginator.get_page(request.GET.get('page'))

    genres    = Genre.objects.all()
    platforms = Platform.objects.all()
    years     = Movie.objects.values_list(
        'release_year', flat=True
    ).distinct().order_by('-release_year').exclude(release_year=None)[:30]

    return render(request, 'movies/search.html', {
        'page_obj':          page_obj,
        'query':             query,
        'genres':            genres,
        'platforms':         platforms,
        'years':             years,
        'selected_type':     selected_type,
        'selected_genre':    selected_genre,
        'selected_platform': selected_platform,
        'selected_year':     selected_year,
        'selected_lang':     selected_lang,
        'selected_sort':     selected_sort,
        'total_results':     movies.count(),
    })

@login_required
def movie_detail_view(request, pk):
    from apps.watchlist.models import WatchlistItem, WatchedMovie

    movie = get_object_or_404(Movie, pk=pk)

    # Auto fetch director and cast from Wikipedia
    # Only fetches ONCE — saves to database after first time
    # Next time loads instantly from database!
    if not movie.director and not movie.cast:
        try:
            from .cast_service import get_cast_and_director
            director, cast = get_cast_and_director(
                movie.title,
                movie.release_year
            )
            if director or cast:
                movie.director = director
                movie.cast     = cast
                movie.save(update_fields=['director', 'cast'])
                print('Fetched cast for: {}'.format(movie.title))
        except Exception as e:
            print('Cast fetch failed: {}'.format(e))

    # Split cast into list for template
    cast_members = []
    if movie.cast:
        cast_members = [
            c.strip()
            for c in movie.cast.split(',')
            if c.strip()
        ]

    in_watchlist = WatchlistItem.objects.filter(
        user=request.user, movie=movie
    ).exists()

    is_watched = WatchedMovie.objects.filter(
        user=request.user, movie=movie
    ).exists()

    similar = get_similar_for_user(request.user, movie, limit=8)
    similar_personalized = user_has_history(request.user)

    streaming_platforms = []
    try:
        from .justwatch_service import sync_platforms_for_movie, get_platform_url
        if not movie.platforms_checked:
            streaming_platforms = sync_platforms_for_movie(movie)
        else:
            streaming_platforms = [
                {
                    'name': p.name,
                    'slug': p.slug,
                    'url':  get_platform_url(p.slug, movie.title),
                }
                for p in movie.platforms.all()
            ]
    except Exception as e:
        print('Platform fetch failed: {}'.format(e))
        if movie.platforms.exists():
            from .justwatch_service import get_platform_url
            streaming_platforms = [
                {
                    'name': p.name,
                    'slug': p.slug,
                    'url':  get_platform_url(p.slug, movie.title),
                }
                for p in movie.platforms.all()
            ]

    return render(request, 'movies/detail.html', {
        'movie':               movie,
        'in_watchlist':        in_watchlist,
        'is_watched':          is_watched,
        'similar':             similar,
        'similar_personalized': similar_personalized,
        'cast_members':        cast_members,
        'streaming_platforms': streaming_platforms,
    })