from django.urls import path
from . import views

urlpatterns = [
    path('movies/', views.movie_list, name='api_movies'),
    path('movies/<int:pk>/', views.movie_detail, name='api_movie_detail'),
    path('search/', views.search_movies, name='api_search'),
    path('watchlist/', views.my_watchlist, name='api_watchlist'),
    path('genres/', views.genre_list, name='api_genres'),
    path('platforms/', views.platform_list, name='api_platforms'),
]
