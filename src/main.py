"""
Command line runner for the Music Recommender Simulation.

This file runs the recommender against a suite of user taste profiles so we can
stress-test the scoring logic. It includes:

- Three "realistic" profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock)
- A set of ADVERSARIAL / edge-case profiles designed to try to "trick" the
  scoring logic (conflicting preferences, impossible targets, empty profile,
  out-of-range values).

Run from the project root with:

    python src/main.py                 # runs every scoring mode
    python src/main.py Genre-First     # runs just one mode
    python src/main.py --plain         # ASCII layout instead of the table

Scoring modes (Challenge 2) are switched by name; see recommender.STRATEGIES.
"""

import sys
import textwrap

from recommender import load_songs, recommend_songs, STRATEGIES, get_strategy


# ---------------------------------------------------------------------------
# Realistic profiles — three distinct, coherent listeners.
# Now also exercise the Challenge 1 advanced attributes.
# ---------------------------------------------------------------------------
REALISTIC_PROFILES = [
    (
        "High-Energy Pop",
        {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.90,
            "target_valence": 0.85,
            "target_danceability": 0.85,
            "target_acousticness": 0.10,
            "target_tempo_bpm": 125,
            "target_popularity": 85,
            "favorite_decade": "2020s",
            "preferred_tags": ["euphoric", "uplifting"],
        },
    ),
    (
        "Chill Lofi",
        {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.40,
            "target_valence": 0.58,
            "target_danceability": 0.60,
            "target_acousticness": 0.80,
            "target_tempo_bpm": 78,
            "target_instrumentalness": 0.85,
            "favorite_language": "instrumental",
            "preferred_tags": ["mellow", "focused", "calm"],
        },
    ),
    (
        "Deep Intense Rock",
        {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.92,
            "target_valence": 0.45,
            "target_danceability": 0.60,
            "target_acousticness": 0.10,
            "target_tempo_bpm": 150,
            "target_popularity": 55,
            "preferred_tags": ["aggressive", "powerful", "driving"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Adversarial / edge-case profiles — designed to probe the scoring logic.
# ---------------------------------------------------------------------------
ADVERSARIAL_PROFILES = [
    # Conflicting "feel": wants maximum energy AND a sad mood AND fully acoustic.
    # High energy usually means low acousticness, so no song can satisfy all of
    # these at once — what does the ranker settle for?
    (
        "Conflicting: High-Energy but Sad & Acoustic",
        {
            "favorite_mood": "sad",
            "target_energy": 0.95,
            "target_valence": 0.10,
            "target_acousticness": 0.95,
            "target_tempo_bpm": 160,
        },
    ),
    # Impossible genre + mismatched feel: asks for an EDM track that is calm,
    # slow, and acoustic. EDM in the catalog is the opposite of all of that.
    (
        "Impossible: Calm Acoustic EDM",
        {
            "favorite_genre": "edm",
            "favorite_mood": "euphoric",
            "target_energy": 0.05,
            "target_valence": 0.20,
            "target_danceability": 0.10,
            "target_acousticness": 0.98,
            "target_tempo_bpm": 60,
        },
    ),
    # Empty profile: no preferences at all. Every song scores 0.0 — does the
    # ranker still return something sane (and stable)?
    (
        "Empty: No Preferences",
        {},
    ),
    # Out-of-range values: energy/valence far outside the expected 0.0-1.0 band
    # and a tempo below the min-max floor. Tests clamping / graceful handling.
    (
        "Out-of-Range: Values Beyond 0-1",
        {
            "favorite_genre": "metal",
            "target_energy": 2.5,
            "target_valence": -1.0,
            "target_acousticness": 5.0,
            "target_tempo_bpm": 400,
        },
    ),
    # Genre-only: a single categorical preference and nothing else. Should the
    # genre match alone be enough to dominate ranking? (Also a good test of the
    # diversity penalty: three of the catalog's songs are hip-hop, two by the
    # same artist.)
    (
        "Genre-Only: hip-hop and nothing else",
        {
            "favorite_genre": "hip-hop",
        },
    ),
]


def main() -> None:
    # Parse tiny CLI: an optional strategy name and an optional --plain flag.
    args = [a for a in sys.argv[1:]]
    plain = "--plain" in args
    args = [a for a in args if a != "--plain"]
    requested = args[0] if args else None

    if requested and requested not in STRATEGIES:
        print(f"Unknown mode '{requested}'. Available: {', '.join(STRATEGIES)}")
        return

    modes = [requested] if requested else list(STRATEGIES)

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for mode in modes:
        strategy = get_strategy(mode)
        print("\n\n" + "#" * 70)
        print(f"##  SCORING MODE: {strategy.name}  -  {strategy.description}")
        print("#" * 70)

        print("\n----- REALISTIC PROFILES -----")
        for name, prefs in REALISTIC_PROFILES:
            recommendations = recommend_songs(prefs, songs, k=5, strategy=strategy)
            print_recommendations(name, prefs, recommendations, plain=plain)

        print("\n----- ADVERSARIAL / EDGE-CASE PROFILES -----")
        for name, prefs in ADVERSARIAL_PROFILES:
            recommendations = recommend_songs(prefs, songs, k=5, strategy=strategy)
            print_recommendations(name, prefs, recommendations, plain=plain)


def print_recommendations(name, user_prefs, recommendations, plain=False) -> None:
    """Print a ranked list of recommendations, as a table by default."""
    header = (f"TOP RECOMMENDATIONS - {name}  "
              f"(for a {user_prefs.get('favorite_genre', 'any')} / "
              f"{user_prefs.get('favorite_mood', 'any')} listener)")

    print()
    print(header)

    if not recommendations:
        print("  No recommendations found.\n")
        return

    if plain:
        _print_plain(recommendations)
    else:
        print(format_recommendations_table(recommendations))


# ---------------------------------------------------------------------------
# Challenge 4: Visual summary table
# ---------------------------------------------------------------------------
def format_recommendations_table(recommendations) -> str:
    """Render recommendations as a table, including the reasons for each score.

    Uses `tabulate` when it's installed for nicely aligned grids, and falls
    back to a dependency-free ASCII table so the program always runs.
    """
    headers = ["#", "Title", "Artist", "Genre / Mood", "Score", "Reasons"]
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append([
            rank,
            song["title"],
            song["artist"],
            f"{song['genre']} / {song['mood']}",
            f"{score:.2f}",
            # Reasons on their own lines so the "why" stays readable.
            "\n".join(f"- {r}" for r in explanation.split("; ")),
        ])

    try:
        from tabulate import tabulate
        return tabulate(rows, headers=headers, tablefmt="grid")
    except ImportError:
        return _ascii_table(headers, rows)


def _ascii_table(headers, rows) -> str:
    """Minimal grid table with per-cell line wrapping (no external deps)."""
    # Column max widths (cap the Reasons column so the table stays terminal-friendly).
    caps = [4, 26, 22, 20, 6, 46]

    def wrap(text, width):
        lines = []
        for part in str(text).split("\n"):
            lines.extend(textwrap.wrap(part, width) or [""])
        return lines

    # Compute the actual width each column needs (bounded by its cap).
    widths = []
    for c, head in enumerate(headers):
        cells = [head] + [str(r[c]) for r in rows]
        longest = max(len(seg) for cell in cells for seg in str(cell).split("\n"))
        widths.append(min(caps[c], longest))

    def sep():
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def render(cells):
        wrapped = [wrap(cells[c], widths[c]) for c in range(len(headers))]
        height = max(len(w) for w in wrapped)
        out = []
        for line_i in range(height):
            parts = []
            for c in range(len(headers)):
                seg = wrapped[c][line_i] if line_i < len(wrapped[c]) else ""
                parts.append(" " + seg.ljust(widths[c]) + " ")
            out.append("|" + "|".join(parts) + "|")
        return "\n".join(out)

    lines = [sep(), render(headers), sep()]
    for r in rows:
        lines.append(render(r))
        lines.append(sep())
    return "\n".join(lines)


def _print_plain(recommendations) -> None:
    """The original nested-bullet layout, kept behind --plain."""
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']}  -  {score:.2f} pts")
        print(f"      {song['artist']}  |  {song['genre']} / {song['mood']}")
        print("      Reasons:")
        for reason in explanation.split("; "):
            print(f"        - {reason}")
    print()


if __name__ == "__main__":
    main()
