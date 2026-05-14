from django.urls import path
from . import views

urlpatterns = [
    path('', views.watchlist_view, name='watchlist'),
    path('toggle/<int:movie_id>/', views.toggle_watchlist, name='toggle_watchlist'),
    path('watched/<int:movie_id>/', views.mark_watched, name='mark_watched'),
    path('remove/<int:item_id>/', views.remove_watchlist, name='remove_watchlist'),
]
