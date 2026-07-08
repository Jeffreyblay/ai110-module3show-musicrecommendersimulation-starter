import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
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

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read the CSV into a list of song dicts, converting numeric columns to int/float."""
    int_fields = {"id", "tempo_bpm"}
    float_fields = {"energy", "valence", "danceability", "acousticness"}

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
                else:
                    song[key] = value
            songs.append(song)
    return songs

# --- Algorithm Recipe weights (tune these for experiments) ---
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
# How much each numeric feature's proximity is worth at most.
NUMERIC_WEIGHTS = {
    "energy": 2.0,          # headline "feel" dimension
    "valence": 1.0,
    "danceability": 1.0,
    "acousticness": 1.0,
    "tempo_bpm": 1.0,
}
# tempo_bpm is min-max scaled into 0-1 before scoring so its large range
# does not dominate the other 0-1 features.
TEMPO_MIN = 60.0
TEMPO_MAX = 170.0


def _scale_tempo(bpm: float) -> float:
    """Min-max scale a BPM value into the 0.0-1.0 range (clamped)."""
    scaled = (bpm - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)
    return min(1.0, max(0.0, scaled))


def _proximity(value: float, target: float) -> float:
    """Reward closeness on a 0-1 scale: 1.0 when value == target, falling to 0.0 as they diverge."""
    return max(0.0, 1.0 - abs(value - target))


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against the profile via the Algorithm Recipe, returning (score, reasons)."""
    score = 0.0
    reasons: List[str] = []

    # Genre match (+2.0, all-or-nothing)
    fav_genre = user_prefs.get("favorite_genre")
    if fav_genre is not None and song.get("genre") == fav_genre:
        score += GENRE_WEIGHT
        reasons.append(f"genre match: {fav_genre} (+{GENRE_WEIGHT:.1f})")

    # Mood match (+1.0, all-or-nothing)
    fav_mood = user_prefs.get("favorite_mood")
    if fav_mood is not None and song.get("mood") == fav_mood:
        score += MOOD_WEIGHT
        reasons.append(f"mood match: {fav_mood} (+{MOOD_WEIGHT:.1f})")

    # Numeric proximity features
    for feature, weight in NUMERIC_WEIGHTS.items():
        target = user_prefs.get(f"target_{feature}")
        if target is None or feature not in song:
            continue

        if feature == "tempo_bpm":
            proximity = _proximity(_scale_tempo(song[feature]),
                                   _scale_tempo(target))
        else:
            proximity = _proximity(song[feature], target)

        points = weight * proximity
        score += points
        reasons.append(f"{feature} close to target ({song[feature]}) (+{points:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, then return the top k as (song, score, explanation) sorted high to low."""
    # Score every song in the catalog. A list comprehension is the Pythonic
    # way to build one list from another.
    scored = [
        (song, *score_song(user_prefs, song))  # -> (song, score, reasons)
        for song in songs
    ]

    # Rank: sort a NEW list highest-score-first. sorted() returns a new list
    # and leaves `songs` untouched; list.sort() would mutate in place and
    # only works on a list you already own. We use sorted() so the caller's
    # catalog keeps its original order.
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    # Take the top k and turn the reasons list into a readable explanation.
    recommendations: List[Tuple[Dict, float, str]] = []
    for song, score, reasons in ranked[:k]:
        explanation = "; ".join(reasons) if reasons else "no strong matches"
        recommendations.append((song, score, explanation))

    return recommendations
