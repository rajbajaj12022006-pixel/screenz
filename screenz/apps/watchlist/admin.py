from django.contrib import admin
from .models import WatchlistItem, WatchedMovie
@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_at')
@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'watched_at')
