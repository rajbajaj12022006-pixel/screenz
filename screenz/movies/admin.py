from django.contrib import admin
from .models import Movie, Genre, Platform, StreamingAvailability


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_year', 'content_type', 'vote_average', 'popularity']
    list_filter = ['content_type', 'release_year', 'genres']
    search_fields = ['title', 'original_title', 'tmdb_id']
    filter_horizontal = ['genres']
    ordering = ['-popularity']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color']


@admin.register(StreamingAvailability)
class StreamingAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['movie', 'platform', 'added_at']
    list_filter = ['platform']
    search_fields = ['movie__title']
