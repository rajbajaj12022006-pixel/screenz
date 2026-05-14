from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Movie, Genre, Platform


def home(request):
    genres = Genre.objects.all()
    platforms = Platform.objects.all()

    # Trending = high popularity
    trending = Movie.objects.prefetch_related('genres', 'platforms').filter(
        vote_count__gte=100
    ).order_by('-popularity')[:12]

    # Newly added to DB
    newly_added = Movie.objects.prefetch_related('genres', 'platforms').order_by(
        '-created_at'
    )[:12]

    # Hero movie
    hero = Movie.objects.filter(vote_count__gte=500, vote_average__gte=7.5).order_by('-popularity').first()

    context = {
        'trending': trending,
        'newly_added': newly_added,
        'genres': genres,
        'platforms': platforms,
        'hero': hero,
        'active_tab': 'home',
    }
    return render(request, 'movies/home.html', context)


def search(request):
    query = request.GET.get('q', '').strip()
    genre_slug = request.GET.get('genre', '')
    content_type = request.GET.get('type', '')
    year = request.GET.get('year', '')
    platform_slug = request.GET.get('platform', '')

    movies = Movie.objects.prefetch_related('genres', 'platforms').filter(adult=False)

    if query:
        movies = movies.filter(
            Q(title__icontains=query) |
            Q(original_title__icontains=query) |
            Q(overview__icontains=query)
        )
    if genre_slug:
        movies = movies.filter(genres__slug=genre_slug)
    if content_type in ('movie', 'tv'):
        movies = movies.filter(content_type=content_type)
    if year:
        movies = movies.filter(release_year=year)
    if platform_slug:
        movies = movies.filter(platforms__slug=platform_slug)

    movies = movies.order_by('-popularity')[:100]

    genres = Genre.objects.all()
    platforms = Platform.objects.all()
    years = range(2025, 1990, -1)

    # HTMX partial response
    if request.htmx:
        return render(request, 'partials/movie_grid.html', {'movies': movies})

    context = {
        'movies': movies,
        'genres': genres,
        'platforms': platforms,
        'years': years,
        'query': query,
        'selected_genre': genre_slug,
        'selected_type': content_type,
        'selected_year': year,
        'selected_platform': platform_slug,
        'result_count': len(movies),
        'active_tab': 'search',
    }
    return render(request, 'movies/search.html', context)


def movie_detail(request, pk):
    movie = get_object_or_404(
        Movie.objects.prefetch_related('genres', 'platforms'),
        pk=pk
    )
    in_watchlist = False
    is_watched = False
    if request.user.is_authenticated:
        from watchlist.models import WatchlistItem
        item = WatchlistItem.objects.filter(user=request.user, movie=movie).first()
        if item:
            in_watchlist = True
            is_watched = item.status == 'watched'

    similar = Movie.objects.filter(
        genres__in=movie.genres.all(), adult=False
    ).exclude(pk=pk).distinct().order_by('-popularity')[:6]

    context = {
        'movie': movie,
        'in_watchlist': in_watchlist,
        'is_watched': is_watched,
        'similar': similar,
        'active_tab': '',
    }
    return render(request, 'movies/detail.html', context)
