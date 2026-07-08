import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py

    The last five fields are the "advanced" attributes added in Challenge 1.
    They carry defaults so existing callers/tests that build a Song with only
    the original nine fields keep working.
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # --- Challenge 1: advanced attributes ---
    instrumentalness: float = 0.0          # 0.0 (vocal) .. 1.0 (instrumental)
    popularity: int = 50                   # 0 (niche) .. 100 (chart-topping)
    release_year: int = 2020               # used to derive the release decade
    language: str = "en"                   # e.g. "en", "instrumental"
    mood_tags: List[str] = field(default_factory=list)  # detailed descriptors

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    New optional fields mirror the advanced song attributes. They default to
    None so the original test profiles remain valid.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # --- Challenge 1: preferences over the advanced attributes ---
    target_popularity: Optional[int] = None
    favorite_decade: Optional[str] = None            # e.g. "2020s"
    favorite_language: Optional[str] = None          # e.g. "instrumental"
    preferred_tags: Optional[List[str]] = None        # e.g. ["nostalgic"]
    target_instrumentalness: Optional[float] = None


def load_songs(csv_path: str) -> List[Dict]:
    """Read the CSV into a list of song dicts, converting numeric columns to int/float."""
    int_fields = {"id", "tempo_bpm", "popularity", "release_year"}
    float_fields = {"energy", "valence", "danceability", "acousticness",
                    "instrumentalness"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song: Dict = {}
            for key, value in row.items():
                value = value.strip()
                if key in int_fields:
                    song[key] = int(value)
                elif key in float_fields:
                    song[key] = float(value)
                elif key == "mood_tags":
                    # Detailed mood tags are stored pipe-separated inside the
                    # single CSV cell so they don't collide with the commas.
                    song[key] = [t.strip() for t in value.split("|") if t.strip()]
                else:
                    song[key] = value
            # Derive the release decade once, up front, so scoring stays simple.
            if "release_year" in song:
                song["release_decade"] = f"{(song['release_year'] // 10) * 10}s"
            songs.append(song)
    return songs


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------
# tempo_bpm and popularity are min-max scaled into 0-1 before scoring so their
# large ranges do not dominate the other 0-1 features.
TEMPO_MIN = 60.0
TEMPO_MAX = 170.0
POPULARITY_MIN = 0.0
POPULARITY_MAX = 100.0


def _scale(value: float, lo: float, hi: float) -> float:
    """Min-max scale a value into the 0.0-1.0 range (clamped)."""
    scaled = (value - lo) / (hi - lo)
    return min(1.0, max(0.0, scaled))


def _scale_tempo(bpm: float) -> float:
    return _scale(bpm, TEMPO_MIN, TEMPO_MAX)


def _proximity(value: float, target: float) -> float:
    """Reward closeness on a 0-1 scale: 1.0 when value == target, falling to 0.0 as they diverge."""
    return max(0.0, 1.0 - abs(value - target))


# ---------------------------------------------------------------------------
# Challenge 2: Scoring modes via a Strategy pattern
# ---------------------------------------------------------------------------
# Each strategy is a small object that owns a set of weights plus a shared
# `score()` method. Callers pick a strategy and stay decoupled from *how* the
# score is built. Adding a new mode = subclass + override a few class
# attributes; no change to score() or recommend_songs() is needed.
class ScoringStrategy:
    """Base scoring strategy. Subclasses tune the weights below.

    Every mode reuses one `score()` implementation; only the weights differ,
    which keeps the ranking behaviour consistent and easy to reason about.
    """

    name: str = "Balanced"
    description: str = "Every signal weighted evenly-ish."

    # Categorical, all-or-nothing matches.
    genre_weight: float = 2.0
    mood_weight: float = 1.0
    decade_weight: float = 1.0
    language_weight: float = 1.0

    # Overlap of detailed mood tags (scaled by how many the user asked for).
    mood_tags_weight: float = 1.5

    # Numeric proximity features (each contributes weight * proximity).
    numeric_weights: Dict[str, float] = {
        "energy": 2.0,
        "valence": 1.0,
        "danceability": 1.0,
        "acousticness": 1.0,
        "instrumentalness": 1.0,
        "tempo_bpm": 1.0,
        "popularity": 1.0,
    }

    # Challenge 3: points subtracted per prior appearance of a song's artist
    # or genre in the already-selected results. 0.0 disables the penalty.
    diversity_penalty: float = 1.25

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        """Score one song against the profile, returning (score, reasons)."""
        score = 0.0
        reasons: List[str] = []

        # --- Categorical matches ---
        fav_genre = user_prefs.get("favorite_genre")
        if fav_genre is not None and song.get("genre") == fav_genre:
            score += self.genre_weight
            reasons.append(f"genre match: {fav_genre} (+{self.genre_weight:.1f})")

        fav_mood = user_prefs.get("favorite_mood")
        if fav_mood is not None and song.get("mood") == fav_mood:
            score += self.mood_weight
            reasons.append(f"mood match: {fav_mood} (+{self.mood_weight:.1f})")

        fav_decade = user_prefs.get("favorite_decade")
        if fav_decade is not None and song.get("release_decade") == fav_decade:
            score += self.decade_weight
            reasons.append(f"decade match: {fav_decade} (+{self.decade_weight:.1f})")

        fav_language = user_prefs.get("favorite_language")
        if fav_language is not None and song.get("language") == fav_language:
            score += self.language_weight
            reasons.append(f"language match: {fav_language} (+{self.language_weight:.1f})")

        # --- Detailed mood tags: reward overlap ---
        preferred_tags = user_prefs.get("preferred_tags")
        if preferred_tags:
            song_tags = set(song.get("mood_tags", []))
            shared = song_tags.intersection(preferred_tags)
            if shared:
                overlap = len(shared) / len(set(preferred_tags))
                points = self.mood_tags_weight * overlap
                score += points
                reasons.append(
                    f"mood tags match {sorted(shared)} (+{points:.2f})"
                )

        # --- Numeric proximity features ---
        for feature, weight in self.numeric_weights.items():
            target = user_prefs.get(f"target_{feature}")
            if target is None or feature not in song:
                continue

            if feature == "tempo_bpm":
                proximity = _proximity(_scale_tempo(song[feature]),
                                       _scale_tempo(target))
            elif feature == "popularity":
                proximity = _proximity(_scale(song[feature], POPULARITY_MIN, POPULARITY_MAX),
                                       _scale(target, POPULARITY_MIN, POPULARITY_MAX))
            else:
                proximity = _proximity(song[feature], target)

            points = weight * proximity
            score += points
            reasons.append(f"{feature} close to target ({song[feature]}) (+{points:.2f})")

        return score, reasons


class GenreFirstStrategy(ScoringStrategy):
    """Genre is king: matching the favourite genre outweighs everything else."""
    name = "Genre-First"
    description = "Heavily favours songs in the user's favourite genre."
    genre_weight = 5.0
    mood_weight = 0.75


class MoodFirstStrategy(ScoringStrategy):
    """Vibe over label: mood and detailed mood tags dominate the ranking."""
    name = "Mood-First"
    description = "Prioritises mood and detailed mood tags over genre."
    genre_weight = 0.75
    mood_weight = 3.0
    mood_tags_weight = 3.0


class EnergyFocusedStrategy(ScoringStrategy):
    """Match the physical feel: energy, tempo and danceability drive the score."""
    name = "Energy-Focused"
    description = "Chases the right energy/tempo/danceability, plays down genre."
    genre_weight = 1.0
    mood_weight = 0.5
    numeric_weights = {
        "energy": 4.0,
        "tempo_bpm": 3.0,
        "danceability": 2.0,
        "valence": 0.5,
        "acousticness": 0.5,
        "instrumentalness": 0.5,
        "popularity": 0.5,
    }


# Registry so callers (main.py) can look strategies up by name.
STRATEGIES: Dict[str, ScoringStrategy] = {
    s.name: s for s in (
        ScoringStrategy(),
        GenreFirstStrategy(),
        MoodFirstStrategy(),
        EnergyFocusedStrategy(),
    )
}
DEFAULT_STRATEGY = STRATEGIES["Balanced"]


def get_strategy(name: Optional[str]) -> ScoringStrategy:
    """Resolve a strategy by name, falling back to the balanced default."""
    if name is None:
        return DEFAULT_STRATEGY
    return STRATEGIES.get(name, DEFAULT_STRATEGY)


def score_song(user_prefs: Dict, song: Dict,
               strategy: Optional[ScoringStrategy] = None) -> Tuple[float, List[str]]:
    """Score one song against the profile using the given strategy (or default)."""
    return (strategy or DEFAULT_STRATEGY).score(user_prefs, song)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    strategy: Optional[ScoringStrategy] = None
                    ) -> List[Tuple[Dict, float, str]]:
    """Score every song, then greedily pick the top k applying a diversity penalty.

    Challenge 3: instead of a plain sort-and-slice, we select songs one at a
    time. Before each pick we subtract a penalty from every candidate for each
    time its artist or genre already appears in the results chosen so far. This
    stops a single artist/genre from monopolising the top of the list while
    still letting a strong enough song win despite the penalty.
    """
    strategy = strategy or DEFAULT_STRATEGY

    # Base scores (strategy-dependent) computed once.
    scored = [(song, *strategy.score(user_prefs, song)) for song in songs]

    recommendations: List[Tuple[Dict, float, str]] = []
    remaining = list(scored)
    artist_counts: Dict[str, int] = {}
    genre_counts: Dict[str, int] = {}

    while remaining and len(recommendations) < k:
        best_i = 0
        best_adj = None
        best_penalty = 0.0
        best_repeats: Tuple[int, int] = (0, 0)

        for i, (song, base, _reasons) in enumerate(remaining):
            a = artist_counts.get(song.get("artist"), 0)
            g = genre_counts.get(song.get("genre"), 0)
            penalty = strategy.diversity_penalty * (a + g)
            adj = base - penalty
            # Highest adjusted score wins; ties keep earlier (higher base) order.
            if best_adj is None or adj > best_adj:
                best_adj, best_i, best_penalty, best_repeats = adj, i, penalty, (a, g)

        song, base, reasons = remaining.pop(best_i)
        reasons = list(reasons)
        if best_penalty > 0:
            a, g = best_repeats
            reasons.append(
                f"diversity penalty (artist x{a}, genre x{g}) (-{best_penalty:.2f})"
            )

        explanation = "; ".join(reasons) if reasons else "no strong matches"
        recommendations.append((song, best_adj, explanation))

        artist_counts[song.get("artist")] = artist_counts.get(song.get("artist"), 0) + 1
        genre_counts[song.get("genre")] = genre_counts.get(song.get("genre"), 0) + 1

    return recommendations


# ---------------------------------------------------------------------------
# OOP wrapper (Song / UserProfile) — required by tests/test_recommender.py.
# It delegates to the functional core above so there is a single source of
# truth for the scoring logic.
# ---------------------------------------------------------------------------
def _song_to_dict(song: Song) -> Dict:
    d = {
        "id": song.id, "title": song.title, "artist": song.artist,
        "genre": song.genre, "mood": song.mood, "energy": song.energy,
        "tempo_bpm": song.tempo_bpm, "valence": song.valence,
        "danceability": song.danceability, "acousticness": song.acousticness,
        "instrumentalness": song.instrumentalness, "popularity": song.popularity,
        "release_year": song.release_year, "language": song.language,
        "mood_tags": song.mood_tags,
    }
    d["release_decade"] = f"{(song.release_year // 10) * 10}s"
    return d


def _profile_to_prefs(user: UserProfile) -> Dict:
    prefs: Dict = {
        "favorite_genre": user.favorite_genre,
        "favorite_mood": user.favorite_mood,
        "target_energy": user.target_energy,
    }
    # likes_acoustic maps to a high/low acousticness target.
    prefs["target_acousticness"] = 0.9 if user.likes_acoustic else 0.1
    for src, dst in (
        ("target_popularity", "target_popularity"),
        ("favorite_decade", "favorite_decade"),
        ("favorite_language", "favorite_language"),
        ("preferred_tags", "preferred_tags"),
        ("target_instrumentalness", "target_instrumentalness"),
    ):
        val = getattr(user, src, None)
        if val is not None:
            prefs[dst] = val
    return prefs


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], strategy: Optional[ScoringStrategy] = None):
        self.songs = songs
        self.strategy = strategy or DEFAULT_STRATEGY

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        prefs = _profile_to_prefs(user)
        song_dicts = [_song_to_dict(s) for s in self.songs]
        ranked = recommend_songs(prefs, song_dicts, k=k, strategy=self.strategy)
        by_id = {s.id: s for s in self.songs}
        return [by_id[song["id"]] for song, _score, _why in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        prefs = _profile_to_prefs(user)
        _score, reasons = score_song(prefs, _song_to_dict(song), self.strategy)
        return "; ".join(reasons) if reasons else "no strong matches"
