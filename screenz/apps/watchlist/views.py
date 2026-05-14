from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.movies.models import Movie
from .models import WatchlistItem, WatchedMovie

@login_required
@require_POST
def toggle_watchlist(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    item, created = WatchlistItem.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        item.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from watchlist'})
    return JsonResponse({'status': 'added', 'message': 'Added to watchlist'})

@login_required
@require_POST
def toggle_watched(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    item, created = WatchedMovie.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        item.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})
