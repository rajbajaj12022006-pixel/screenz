from django.urls import path
from . import views
urlpatterns = [
    path('toggle/<int:pk>/', views.toggle_watchlist, name='toggle_watchlist'),
    path('watched/<int:pk>/', views.toggle_watched, name='toggle_watched'),
]
