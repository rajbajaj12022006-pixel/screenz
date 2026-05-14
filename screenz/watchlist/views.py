from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import WatchlistItem
from movies.models import Movie


@login_required
def watchlist_view(request):
    items = WatchlistItem.objects.filter(
        user=request.user, status='want_to_watch'
    ).select_related('movie').prefetch_related('movie__genres', 'movie__platforms')
    return render(request, 'watchlist/watchlist.html', {'items': items, 'active_tab': 'watchlist'})


@login_required
@require_POST
def toggle_watchlist(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    item, created = WatchlistItem.objects.get_or_create(
        user=request.user, movie=movie,
        defaults={'status': 'want_to_watch'}
    )
    if not created:
        item.delete()
        in_list = False
    else:
        in_list = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'in_watchlist': in_list, 'movie_id': movie_id})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def mark_watched(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    item, _ = WatchlistItem.objects.get_or_create(user=request.user, movie=movie)
    item.status = 'watched'
    item.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'watched', 'movie_id': movie_id})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def remove_watchlist(request, item_id):
    item = get_object_or_404(WatchlistItem, pk=item_id, user=request.user)
    item.delete()
    return redirect('watchlist')
