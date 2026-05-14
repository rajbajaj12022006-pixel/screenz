from django.db import models
from django.conf import settings
from movies.models import Movie


class WatchlistItem(models.Model):
    STATUS_CHOICES = [
        ('want_to_watch', 'Want to Watch'),
        ('watched', 'Watched'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist_items')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlist_items')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='want_to_watch')
    rating = models.IntegerField(null=True, blank=True)  # User's personal rating 1-10
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.movie.title} ({self.status})"
