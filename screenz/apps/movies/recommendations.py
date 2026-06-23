"""
Content-based movie recommendations using sklearn.
Build index: python manage.py build_recommendation_index
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import joblib
import numpy as np
from django.conf import settings
from django.utils import timezone
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, normalize

from .models import Movie

INDEX_PATH = settings.BASE_DIR / 'data' / 'recommendation_index.joblib'
WATCHED_WEIGHT = 1.0
WATCHLIST_WEIGHT = 0.5
NEIGHBOR_POOL = 30

_index_cache: Optional['MovieIndex'] = None


@dataclass
class MovieIndex:
    movie_ids: list[int]
    feature_matrix: csr_matrix
    movie_count: int
    latest_added_at: Optional[str]
    id_to_idx: dict[int, int]
    knn: Optional[NearestNeighbors] = None

    def idx_for(self, movie_id: int) -> Optional[int]:
        return self.id_to_idx.get(movie_id)


def _index_path() -> str:
    os.makedirs(settings.BASE_DIR / 'data', exist_ok=True)
    return str(INDEX_PATH)


def _latest_movie_meta():
    latest = Movie.objects.order_by('-added_at').values_list('added_at', flat=True).first()
    return Movie.objects.count(), latest.isoformat() if latest else None


def _movie_text(movie: Movie) -> str:
    return '{} {}'.format(movie.title or '', movie.overview or '').strip()


def _movie_genre_slugs(movie: Movie) -> list[str]:
    return [g.slug for g in movie.genres.all()]


def build_movie_index() -> MovieIndex:
    movies = list(
        Movie.objects.prefetch_related('genres').order_by('pk')
    )
    if not movies:
        raise ValueError('No movies in database to build recommendation index.')

    movie_ids = [m.pk for m in movies]
    texts = [_movie_text(m) for m in movies]
    genre_lists = [_movie_genre_slugs(m) for m in movies]
    numerics = np.array([
        [
            m.vote_average or 0.0,
            m.popularity or 0.0,
            float(m.release_year or 0),
        ]
        for m in movies
    ], dtype=np.float64)

    tfidf = TfidfVectorizer(max_features=500, stop_words='english')
    text_matrix = tfidf.fit_transform(texts)

    mlb = MultiLabelBinarizer()
    genre_matrix = mlb.fit_transform(genre_lists)

    scaler = StandardScaler()
    numeric_matrix = scaler.fit_transform(numerics)

    feature_matrix = hstack([
        text_matrix,
        csr_matrix(genre_matrix),
        csr_matrix(numeric_matrix),
    ])
    feature_matrix = normalize(feature_matrix, norm='l2', axis=1)

    knn = NearestNeighbors(
        metric='cosine',
        algorithm='brute',
        n_neighbors=min(NEIGHBOR_POOL + 1, len(movie_ids)),
    )
    knn.fit(feature_matrix)

    movie_count, latest_added_at = _latest_movie_meta()
    index = MovieIndex(
        movie_ids=movie_ids,
        feature_matrix=feature_matrix,
        movie_count=movie_count,
        latest_added_at=latest_added_at,
        id_to_idx={mid: i for i, mid in enumerate(movie_ids)},
        knn=knn,
    )

    payload = {
        'index': index,
        'tfidf': tfidf,
        'mlb': mlb,
        'scaler': scaler,
        'built_at': timezone.now().isoformat(),
    }
    joblib.dump(payload, _index_path())
    global _index_cache
    _index_cache = index
    return index


def load_movie_index(*, rebuild_if_stale: bool = True) -> MovieIndex:
    global _index_cache
    if _index_cache is not None:
        current_count, latest_added_at = _latest_movie_meta()
        if (
            _index_cache.movie_count == current_count
            and _index_cache.latest_added_at == latest_added_at
        ):
            return _index_cache

    path = _index_path()
    if os.path.exists(path):
        payload = joblib.load(path)
        index = payload['index']
        current_count, latest_added_at = _latest_movie_meta()
        if (
            not rebuild_if_stale
            or (
                index.movie_count == current_count
                and index.latest_added_at == latest_added_at
            )
        ):
            _index_cache = index
            return index

    return build_movie_index()


def _get_knn(index: MovieIndex) -> NearestNeighbors:
    if index.knn is not None:
        return index.knn
    knn = NearestNeighbors(
        metric='cosine',
        algorithm='brute',
        n_neighbors=min(NEIGHBOR_POOL + 1, len(index.movie_ids)),
    )
    knn.fit(index.feature_matrix)
    index.knn = knn
    return knn


def _user_interactions(user):
    from apps.watchlist.models import WatchlistItem, WatchedMovie

    watched = list(
        WatchedMovie.objects.filter(user=user).select_related('movie')
    )
    watchlist = list(
        WatchlistItem.objects.filter(user=user).select_related('movie')
    )
    return watched, watchlist


def _user_has_history(user) -> bool:
    watched, watchlist = _user_interactions(user)
    return bool(watched or watchlist)


def _user_taste_vector(index: MovieIndex, user) -> Optional[csr_matrix]:
    watched, watchlist = _user_interactions(user)
    if not watched and not watchlist:
        return None

    vectors = []
    weights = []

    for item in watched:
        idx = index.idx_for(item.movie_id)
        if idx is None:
            continue
        weight = WATCHED_WEIGHT
        if item.rating:
            weight *= item.rating / 5.0
        vectors.append(index.feature_matrix[idx])
        weights.append(weight)

    watched_ids = {item.movie_id for item in watched}
    for item in watchlist:
        if item.movie_id in watched_ids:
            continue
        idx = index.idx_for(item.movie_id)
        if idx is None:
            continue
        vectors.append(index.feature_matrix[idx])
        weights.append(WATCHLIST_WEIGHT)

    if not vectors:
        return None

    weights = np.array(weights, dtype=np.float64)
    weights /= weights.sum()

    taste = vectors[0].multiply(weights[0])
    for vec, weight in zip(vectors[1:], weights[1:]):
        taste = taste + vec.multiply(weight)
    return normalize(taste, norm='l2')


def _exclude_ids(user) -> set[int]:
    from apps.watchlist.models import WatchlistItem, WatchedMovie

    watched_ids = set(
        WatchedMovie.objects.filter(user=user).values_list('movie_id', flat=True)
    )
    watchlist_ids = set(
        WatchlistItem.objects.filter(user=user).values_list('movie_id', flat=True)
    )
    return watched_ids | watchlist_ids


def _movies_by_ids(movie_ids: list[int]) -> list[Movie]:
    if not movie_ids:
        return []
    movies = Movie.objects.filter(pk__in=movie_ids).prefetch_related('genres', 'platforms')
    by_id = {m.pk: m for m in movies}
    return [by_id[mid] for mid in movie_ids if mid in by_id]


def user_has_history(user) -> bool:
    return _user_has_history(user)


def get_recommendations_for_user(user, limit: int = 12) -> list[Movie]:
    if not _user_has_history(user):
        return list(
            Movie.objects.filter(vote_average__gte=7.0)
            .order_by('-popularity')[:limit]
        )

    index = load_movie_index()
    taste = _user_taste_vector(index, user)
    if taste is None:
        return list(
            Movie.objects.filter(vote_average__gte=7.0)
            .order_by('-popularity')[:limit]
        )

    scores = cosine_similarity(taste, index.feature_matrix).ravel()
    exclude = _exclude_ids(user)
    ranked_ids = []

    for idx in np.argsort(scores)[::-1]:
        movie_id = index.movie_ids[idx]
        if movie_id in exclude:
            continue
        ranked_ids.append(movie_id)
        if len(ranked_ids) >= limit:
            break

    return _movies_by_ids(ranked_ids)


def get_similar_for_user(user, movie: Movie, limit: int = 8) -> list[Movie]:
    index = load_movie_index()
    movie_idx = index.idx_for(movie.pk)
    if movie_idx is None:
        return list(
            Movie.objects.filter(
                genres__in=movie.genres.all(),
                content_type=movie.content_type,
            )
            .exclude(pk=movie.pk)
            .distinct()
            .order_by('-vote_average')[:limit]
        )

    knn = _get_knn(index)
    distances, indices = knn.kneighbors(
        index.feature_matrix[movie_idx],
        n_neighbors=min(NEIGHBOR_POOL + 1, len(index.movie_ids)),
    )
    neighbor_indices = [
        i for i in indices[0]
        if index.movie_ids[i] != movie.pk
    ]

    if _user_has_history(user):
        taste = _user_taste_vector(index, user)
        if taste is not None:
            neighbor_vecs = index.feature_matrix[neighbor_indices]
            taste_scores = cosine_similarity(taste, neighbor_vecs).ravel()
            neighbor_indices = [
                neighbor_indices[i]
                for i in np.argsort(taste_scores)[::-1]
            ]

    ranked_ids = []
    for idx in neighbor_indices:
        ranked_ids.append(index.movie_ids[idx])
        if len(ranked_ids) >= limit:
            break

    return _movies_by_ids(ranked_ids)
