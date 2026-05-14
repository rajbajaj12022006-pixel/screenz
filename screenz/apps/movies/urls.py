from django.urls import path
from . import views
urlpatterns = [
    path('', views.home_view, name='home'),
    path('search/', views.search_view, name='search'),
    path('movie/<int:pk>/', views.movie_detail_view, name='movie_detail'),
]
