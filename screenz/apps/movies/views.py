from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Movie, Genre, Platform

@login_required
def home_view(request):
    trending = Movie.objects.filter(vote_average__gte=7.0).order_by('-popularity')[:10]
    new_movies = Movie.objects.filter(content_type='movie').order_by('-added_at')[:10]
    new_shows = Movie.objects.filter(content_type='tv').order_by('-added_at')[:10]
    genres = Genre.objects.all()
    platforms = Platform.objects.all()
    return render(request, 'movies/home.html', {
        'trending': trending,
        'new_movies': new_movies,
        'new_shows': new_shows,
        'genres': genres,
        'platforms': platforms,
    })

@login_required
def search_view(request):
    query = request.GET.get('q', '').strip()
    genre_id = request.GET.get('genre', '')
    platform_slug = request.GET.get('platform', '')
    content_type = request.GET.get('type', '')
    year = request.GET.get('year', '')
    sort = request.GET.get('sort', '-popularity')

    movies = Movie.objects.all()

    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(overview__icontains=query))
    if genre_id:
        movies = movies.filter(genres__id=genre_id)
    if platform_slug:
        movies = movies.filter(platforms__slug=platform_slug)
    if content_type in ('movie', 'tv'):
        movies = movies.filter(content_type=content_type)
    if year:
        movies = movies.filter(release_year=year)

    SORT_OPTIONS = {
        '-popularity': '-popularity',
        '-vote_average': '-vote_average',
        '-release_year': '-release_year',
        'title': 'title',
    }
    movies = movies.order_by(SORT_OPTIONS.get(sort, '-popularity')).distinct()

    paginator = Paginator(movies, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    genres = Genre.objects.all()
    platforms = Platform.objects.all()
    years = Movie.objects.values_list('release_year', flat=True).distinct().order_by('-release_year').exclude(release_year=None)[:30]

    return render(request, 'movies/search.html', {
        'page_obj': page_obj,
        'query': query,
        'genres': genres,
        'platforms': platforms,
        'years': years,
        'selected_genre': genre_id,
        'selected_platform': platform_slug,
        'selected_type': content_type,
        'selected_year': year,
        'selected_sort': sort,
        'total_results': movies.count(),
    })

@login_required
def movie_detail_view(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    from apps.watchlist.models import WatchlistItem, WatchedMovie
    in_watchlist = WatchlistItem.objects.filter(user=request.user, movie=movie).exists()
    is_watched = WatchedMovie.objects.filter(user=request.user, movie=movie).exists()
    cast_members = [member.strip() for member in (movie.cast or '').split(',') if member.strip()]
    similar = Movie.objects.filter(
        genres__in=movie.genres.all(), content_type=movie.content_type
    ).exclude(pk=movie.pk).distinct().order_by('-vote_average')[:8]
    return render(request, 'movies/detail.html', {
        'movie': movie, 'in_watchlist': in_watchlist,
        'is_watched': is_watched, 'similar': similar, 'cast_members': cast_members,
    })
