from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Platform(models.Model):
    PLATFORM_CHOICES = [
        ('netflix',  'Netflix'),
        ('prime',    'Amazon Prime Video'),
        ('jio',      'JioCinema'),
        ('hotstar',  'Disney+ Hotstar'),
        ('apple',    'Apple TV+'),
        ('zee5',     'ZEE5'),
        ('sonyliv',  'SonyLIV'),
        ('other',    'Other'),
    ]
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=50, choices=PLATFORM_CHOICES, unique=True)
    logo = models.ImageField(upload_to='platforms/', null=True, blank=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    TYPE_CHOICES = [('movie', 'Movie'), ('tv', 'TV Show')]

    tmdb_id            = models.IntegerField(unique=True, null=True, blank=True)
    title              = models.CharField(max_length=500, db_index=True)
    original_title     = models.CharField(max_length=500, blank=True)
    overview           = models.TextField(blank=True)
    tagline            = models.CharField(max_length=500, blank=True)
    content_type       = models.CharField(max_length=10, choices=TYPE_CHOICES, default='movie', db_index=True)
    genres             = models.ManyToManyField(Genre, blank=True, related_name='movies')
    platforms          = models.ManyToManyField(Platform, blank=True, related_name='movies')
    release_date       = models.DateField(null=True, blank=True, db_index=True)
    release_year       = models.IntegerField(null=True, blank=True, db_index=True)
    runtime            = models.IntegerField(null=True, blank=True, help_text='Minutes')
    vote_average       = models.FloatField(default=0.0, db_index=True)
    vote_count         = models.IntegerField(default=0)
    popularity         = models.FloatField(default=0.0, db_index=True)
    poster_path        = models.CharField(max_length=500, blank=True)
    backdrop_path      = models.CharField(max_length=500, blank=True)
    original_language  = models.CharField(max_length=10, blank=True, db_index=True)
    budget             = models.BigIntegerField(null=True, blank=True)
    revenue            = models.BigIntegerField(null=True, blank=True)
    status             = models.CharField(max_length=50, blank=True)
    adult              = models.BooleanField(default=False)

    # NEW FIELDS
    trailer_youtube_key = models.CharField(
        max_length=50, blank=True,
        help_text='YouTube video ID — e.g. dQw4w9WgXcQ (from youtube.com/watch?v=THIS_PART)'
    )
    director = models.CharField(
        max_length=300, blank=True,
        help_text='Director name(s)'
    )
    cast = models.TextField(
        blank=True,
        help_text='Comma separated actor names — e.g. Tom Hanks, Brad Pitt, Leonardo DiCaprio'
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['release_year', 'vote_average']),
            models.Index(fields=['content_type', 'release_year']),
            models.Index(fields=['popularity']),
        ]
        ordering = ['-popularity']

    def __str__(self):
        return '{} ({})'.format(self.title, self.release_year)

    @property
    def poster_url(self):
        if self.poster_path:
            return 'https://image.tmdb.org/t/p/w500{}'.format(self.poster_path)
        return '/static/images/no-poster.png'

    @property
    def backdrop_url(self):
        if self.backdrop_path:
            return 'https://image.tmdb.org/t/p/w1280{}'.format(self.backdrop_path)
        return None

    @property
    def runtime_display(self):
        if self.runtime:
            h, m = divmod(self.runtime, 60)
            if h:
                return '{}h {}m'.format(h, m)
            return '{}m'.format(m)
        return 'N/A'