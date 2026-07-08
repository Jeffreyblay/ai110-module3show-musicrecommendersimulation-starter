"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Taste profile: a "chill lofi listener".
    # Categorical targets say WHAT they like; numeric targets (0.0-1.0, plus
    # tempo in BPM) say HOW it should feel, which lets the recommender rank
    # songs that share a genre and separate very different styles.
    user_prefs = {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.40,
        "target_valence": 0.58,
        "target_danceability": 0.60,
        "target_acousticness": 0.80,
        "target_tempo_bpm": 78,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print_recommendations(user_prefs, recommendations)


def print_recommendations(user_prefs, recommendations) -> None:
    """Print a clean, readable ranked list of recommendations."""
    width = 60

    print()
    print("=" * width)
    print("  TOP RECOMMENDATIONS")
    print(f"  for a {user_prefs.get('favorite_genre', 'any')} / "
          f"{user_prefs.get('favorite_mood', 'any')} listener")
    print("=" * width)

    if not recommendations:
        print("\n  No recommendations found.\n")
        return

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']}  -  {score:.2f} pts")
        print(f"      {song['artist']}  |  {song['genre']} / {song['mood']}")
        print("      Reasons:")
        for reason in explanation.split("; "):
            print(f"        - {reason}")

    print("\n" + "=" * width)


if __name__ == "__main__":
    main()
