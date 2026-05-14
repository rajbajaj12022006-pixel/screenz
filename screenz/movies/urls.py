from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
]
