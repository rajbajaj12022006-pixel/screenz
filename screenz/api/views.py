from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from movies.models import Movie, Genre, Platform
from watchlist.models import WatchlistItem
from .serializers import MovieListSerializer, MovieDetailSerializer, WatchlistSerializer, GenreSerializer, PlatformSerializer


class MoviePagination(PageNumberPagination):
    page_size = 20


@api_view(['GET'])
def movie_list(request):
    movies = Movie.objects.prefetch_related('genres', 'platforms').order_by('-popularity')
    paginator = MoviePagination()
    result = paginator.paginate_queryset(movies, request)
    serializer = MovieListSerializer(result, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def movie_detail(request, pk):
    try:
        movie = Movie.objects.prefetch_related('genres', 'platforms').get(pk=pk)
    except Movie.DoesNotExist:
        return Response({'error': 'Movie not found'}, status=404)
    serializer = MovieDetailSerializer(movie)
    return Response(serializer.data)


@api_view(['GET'])
def search_movies(request):
    q = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '')
    content_type = request.GET.get('type', '')
    year = request.GET.get('year', '')
    platform = request.GET.get('platform', '')

    movies = Movie.objects.prefetch_related('genres', 'platforms').filter(adult=False)

    if q:
        movies = movies.filter(Q(title__icontains=q) | Q(overview__icontains=q))
    if genre:
        movies = movies.filter(genres__slug=genre)
    if content_type in ('movie', 'tv'):
        movies = movies.filter(content_type=content_type)
    if year:
        movies = movies.filter(release_year=year)
    if platform:
        movies = movies.filter(platforms__slug=platform)

    movies = movies.order_by('-popularity')
    paginator = MoviePagination()
    result = paginator.paginate_queryset(movies, request)
    serializer = MovieListSerializer(result, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_watchlist(request):
    items = WatchlistItem.objects.filter(user=request.user).select_related('movie').prefetch_related('movie__genres', 'movie__platforms')
    serializer = WatchlistSerializer(items, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def genre_list(request):
    genres = Genre.objects.all()
    return Response(GenreSerializer(genres, many=True).data)


@api_view(['GET'])
def platform_list(request):
    platforms = Platform.objects.all()
    return Response(PlatformSerializer(platforms, many=True).data)
