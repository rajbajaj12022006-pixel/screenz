from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Platform(models.Model):
    PLATFORM_CHOICES = [
        ('netflix', 'Netflix'),
        ('prime', 'Amazon Prime Video'),
        ('jio', 'JioCinema'),
        ('hotstar', 'Disney+ Hotstar'),
        ('apple', 'Apple TV+'),
        ('zee5', 'ZEE5'),
        ('sonyliv', 'SonyLIV'),
    ]
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=50, choices=PLATFORM_CHOICES, unique=True)
    color = models.CharField(max_length=7, default='#E5383B')
    logo_text = models.CharField(max_length=5, default='N')

    def __str__(self):
        return self.name


class Movie(models.Model):
    TYPE_CHOICES = [('movie', 'Movie'), ('tv', 'TV Show')]

    tmdb_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=500, db_index=True)
    original_title = models.CharField(max_length=500, blank=True)
    overview = models.TextField(blank=True)
    tagline = models.CharField(max_length=500, blank=True)
    release_date = models.DateField(null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True, db_index=True)
    runtime = models.IntegerField(null=True, blank=True)  # minutes
    vote_average = models.FloatField(default=0.0, db_index=True)
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0.0, db_index=True)
    poster_path = models.CharField(max_length=200, blank=True)
    backdrop_path = models.CharField(max_length=200, blank=True)
    content_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='movie', db_index=True)
    budget = models.BigIntegerField(default=0)
    revenue = models.BigIntegerField(default=0)
    original_language = models.CharField(max_length=10, blank=True)
    adult = models.BooleanField(default=False)

    genres = models.ManyToManyField(Genre, blank=True)
    platforms = models.ManyToManyField(Platform, through='StreamingAvailability', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-popularity']
        indexes = [
            models.Index(fields=['release_year', 'vote_average']),
            models.Index(fields=['content_type', 'popularity']),
        ]

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    @property
    def poster_url(self):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w342{self.poster_path}"
        return None

    @property
    def backdrop_url(self):
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/w780{self.backdrop_path}"
        return None

    @property
    def runtime_display(self):
        if not self.runtime:
            return ''
        h, m = divmod(self.runtime, 60)
        return f"{h}h {m}m" if h else f"{m}m"


class StreamingAvailability(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True)

    class Meta:
        unique_together = ('movie', 'platform')

    def __str__(self):
        return f"{self.movie.title} on {self.platform.name}"
