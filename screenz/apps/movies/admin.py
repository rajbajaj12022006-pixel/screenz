from django.contrib import admin
from .models import Movie, Genre, Platform

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'content_type', 'vote_average', 'popularity')
    list_filter = ('content_type', 'release_year', 'genres')
    search_fields = ('title', 'tmdb_id')
    filter_horizontal = ('genres', 'platforms')

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
