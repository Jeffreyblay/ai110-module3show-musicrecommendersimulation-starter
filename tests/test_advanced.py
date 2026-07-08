"""
Tests for the stretch-challenge features:

- Challenge 1: advanced song attributes + scoring that uses them
- Challenge 2: multiple scoring modes (Strategy pattern)
- Challenge 3: diversity / fairness penalty
- Challenge 4: the table formatter includes reasons

These exercise both the functional core (load_songs / score_song /
recommend_songs) and the OOP wrapper (Song / UserProfile / Recommender).
"""

import os

from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    ScoringStrategy,
    GenreFirstStrategy,
    MoodFirstStrategy,
    load_songs,
    score_song,
    recommend_songs,
    get_strategy,
    STRATEGIES,
    DEFAULT_STRATEGY,
)

DATA_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _song(**overrides):
    """Build a song dict with sensible defaults, overriding per test."""
    base = {
        "id": 1,
        "title": "Track",
        "artist": "Artist",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.5,
        "tempo_bpm": 100,
        "valence": 0.5,
        "danceability": 0.5,
        "acousticness": 0.5,
        "instrumentalness": 0.5,
        "popularity": 50,
        "release_year": 2020,
        "release_decade": "2020s",
        "language": "en",
        "mood_tags": [],
    }
    base.update(overrides)
    return base


class NoDiversityStrategy(ScoringStrategy):
    """Balanced weights but with the diversity penalty switched off."""
    name = "NoDiversity"
    diversity_penalty = 0.0


# ---------------------------------------------------------------------------
# Challenge 1: advanced attributes are loaded and scored
# ---------------------------------------------------------------------------
def test_load_songs_parses_advanced_attributes():
    songs = load_songs(DATA_CSV)
    assert len(songs) == 20

    first = songs[0]
    # New columns are present and correctly typed.
    assert isinstance(first["popularity"], int)
    assert isinstance(first["release_year"], int)
    assert isinstance(first["instrumentalness"], float)
    assert isinstance(first["mood_tags"], list) and first["mood_tags"]
    # Decade is derived from the release year.
    assert first["release_decade"] == f"{(first['release_year'] // 10) * 10}s"


def test_decade_match_adds_points():
    song = _song(release_year=2021, release_decade="2020s")
    with_match, _ = score_song({"favorite_decade": "2020s"}, song)
    without_match, _ = score_song({"favorite_decade": "1990s"}, song)
    assert with_match > without_match


def test_language_match_adds_points():
    song = _song(language="instrumental")
    matched, reasons = score_song({"favorite_language": "instrumental"}, song)
    unmatched, _ = score_song({"favorite_language": "en"}, song)
    assert matched > unmatched
    assert any("language" in r for r in reasons)


def test_mood_tags_overlap_scales_with_fraction_matched():
    # Overlap is normalised by how many tags the user asked for, so the score
    # reflects the *fraction* of the user's wishes the song satisfies.
    song = _song(mood_tags=["nostalgic", "warm", "smooth"])
    full, _ = score_song({"preferred_tags": ["nostalgic", "warm"]}, song)      # 2/2
    partial, _ = score_song({"preferred_tags": ["nostalgic", "aggressive"]}, song)  # 1/2
    none, _ = score_song({"preferred_tags": ["aggressive"]}, song)             # 0/1
    assert full > partial > none == 0.0


def test_popularity_proximity_is_scaled_not_dominant():
    """A perfect popularity match must not swamp the 0-1 features."""
    song = _song(popularity=100)
    score, reasons = score_song({"target_popularity": 100}, song)
    # Popularity contributes its full weight (1.0) at most, despite the 0-100 range.
    assert any("popularity" in r for r in reasons)
    assert score <= DEFAULT_STRATEGY.numeric_weights["popularity"] + 1e-9


def test_instrumentalness_proximity_rewards_closeness():
    near = _song(instrumentalness=0.9)
    far = _song(instrumentalness=0.1)
    near_score, _ = score_song({"target_instrumentalness": 0.9}, near)
    far_score, _ = score_song({"target_instrumentalness": 0.9}, far)
    assert near_score > far_score


# ---------------------------------------------------------------------------
# Challenge 2: scoring modes (Strategy pattern)
# ---------------------------------------------------------------------------
def test_registry_contains_all_modes():
    assert set(STRATEGIES) == {"Balanced", "Genre-First", "Mood-First", "Energy-Focused"}


def test_get_strategy_falls_back_to_default_on_unknown():
    assert get_strategy(None) is DEFAULT_STRATEGY
    assert get_strategy("does-not-exist") is DEFAULT_STRATEGY
    assert get_strategy("Genre-First").name == "Genre-First"


def test_genre_first_weights_genre_more_than_balanced():
    song = _song(genre="pop")
    prefs = {"favorite_genre": "pop"}
    balanced, _ = score_song(prefs, song, strategy=STRATEGIES["Balanced"])
    genre_first, _ = score_song(prefs, song, strategy=GenreFirstStrategy())
    assert genre_first > balanced


def test_modes_produce_different_rankings():
    songs = load_songs(DATA_CSV)
    # A listener whose genre and energy point at different songs.
    prefs = {"favorite_genre": "hip-hop", "target_energy": 0.98, "target_tempo_bpm": 168}
    genre_top = recommend_songs(prefs, songs, k=1, strategy=STRATEGIES["Genre-First"])[0][0]
    energy_top = recommend_songs(prefs, songs, k=1, strategy=STRATEGIES["Energy-Focused"])[0][0]
    assert genre_top["genre"] == "hip-hop"          # genre mode honours the genre
    assert energy_top["id"] != genre_top["id"]      # energy mode picks something else


# ---------------------------------------------------------------------------
# Challenge 3: diversity / fairness penalty
# ---------------------------------------------------------------------------
def _diversity_catalog():
    # Three identical-artist/genre pop songs (all score the genre match) plus
    # two neutral songs that score nothing.
    return [
        _song(id=1, artist="Popstar", genre="pop"),
        _song(id=2, artist="Popstar", genre="pop"),
        _song(id=3, artist="Popstar", genre="pop"),
        _song(id=4, artist="Other A", genre="jazz"),
        _song(id=5, artist="Other B", genre="rock"),
    ]


def test_diversity_penalty_limits_same_artist_in_top_results():
    songs = _diversity_catalog()
    prefs = {"favorite_genre": "pop"}

    top3 = recommend_songs(prefs, songs, k=3, strategy=ScoringStrategy())
    artists = [s["artist"] for s, _score, _why in top3]
    # The penalty should stop one artist from taking every slot.
    assert artists.count("Popstar") < 3


def test_disabling_penalty_lets_one_artist_dominate():
    songs = _diversity_catalog()
    prefs = {"favorite_genre": "pop"}

    top3 = recommend_songs(prefs, songs, k=3, strategy=NoDiversityStrategy())
    artists = [s["artist"] for s, _score, _why in top3]
    # With no penalty, all three genre matches (same artist) win the top slots.
    assert artists.count("Popstar") == 3


def test_penalty_is_reported_in_reasons():
    # Only same-artist/genre songs exist, so the later picks are *forced* to
    # take a penalty — and that penalty must show up in the reasons.
    songs = [
        _song(id=1, artist="Popstar", genre="pop"),
        _song(id=2, artist="Popstar", genre="pop"),
        _song(id=3, artist="Popstar", genre="pop"),
    ]
    prefs = {"favorite_genre": "pop"}
    top = recommend_songs(prefs, songs, k=3, strategy=ScoringStrategy())
    assert any("diversity penalty" in why for _s, _score, why in top)


# ---------------------------------------------------------------------------
# OOP wrapper still works with the new attributes
# ---------------------------------------------------------------------------
def test_recommender_uses_new_profile_fields():
    songs = [
        Song(1, "Vocal Pop", "A", "pop", "happy", 0.8, 120, 0.9, 0.8, 0.2,
             instrumentalness=0.05, mood_tags=["euphoric"]),
        Song(2, "Instrumental Lofi", "B", "lofi", "chill", 0.4, 80, 0.6, 0.5, 0.9,
             instrumentalness=0.95, mood_tags=["calm"]),
    ]
    user = UserProfile(
        favorite_genre="lofi",
        favorite_mood="chill",
        target_energy=0.4,
        likes_acoustic=True,
        target_instrumentalness=0.95,
        preferred_tags=["calm"],
    )
    rec = Recommender(songs)
    results = rec.recommend(user, k=2)
    assert results[0].id == 2          # the instrumental lofi track wins
    assert rec.explain_recommendation(user, results[0]).strip() != ""
