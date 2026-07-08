# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders (Spotify, YouTube, Netflix) work by turning both the
items and the user into data, then measuring how well they match. They don't
"understand" music the way a person does — they compare numbers that stand in
for taste, such as how energetic or acoustic a track is, and they blend that
with signals like what similar users enjoyed. My version is a **content-based**
recommender: it looks only at the features of each song and how close they are
to a user's stated preferences. It prioritizes **proximity over magnitude** — a
song scores highest when its values are *closest* to what the user likes, not
when they are simply high or low. This keeps the logic transparent and easy to
explain, which matters more here than raw accuracy on a tiny catalog.

The system is built from two separate rules:

- **Scoring** looks at one song at a time and measures how well it matches the
  user. For each numeric feature it uses a proximity score
  (`score = 1 − |song_value − user_preference|`), so a song's energy scores best
  when it sits right on the user's preferred energy. Feature scores are combined
  into a single weighted match score.
- **Ranking** looks at all the scored songs together and decides what to show —
  sorting highest-first, taking the top N, and breaking ties. Keeping this
  separate from scoring means I can change *how many* songs I show without
  touching *how I measure* a match.

### Features used

**`Song`** (from `data/songs.csv`):

- `genre`, `mood` — categorical style cues
- `energy`, `valence`, `danceability`, `acousticness` — numeric, already on a
  0–1 scale, used as the core of the proximity score
- `tempo_bpm` — numeric (min-max scaled to 0–1 before scoring so its large range
  doesn't dominate)
- `id`, `title`, `artist` — identifiers for display only, not used in scoring

**`UserProfile`**:

- A preferred value for each numeric feature (e.g. preferred `energy = 0.40`)
- Optional preferred `genre` / `mood`
- Optional per-feature weights, so some features count more than others in the
  combined score

### Algorithm Recipe

Each song earns points against the user profile, then the songs are ranked by
total score. Categorical matches are all-or-nothing; numeric features award
partial credit based on how *close* they are to the user's target (proximity,
not magnitude).

```
total_score(song, user) =
    +2.0   if song.genre == user.favorite_genre        # genre match
    +1.0   if song.mood  == user.favorite_mood          # mood match
    +2.0 * (1 - |song.energy       - target_energy|)    # energy proximity
    +1.0 * (1 - |song.valence      - target_valence|)   # valence proximity
    +1.0 * (1 - |song.danceability - target_danceability|)
    +1.0 * (1 - |song.acousticness - target_acousticness|)
    +1.0 * (1 - |scaled_tempo      - target_tempo_scaled|)  # tempo (min-max 0-1)
```

| Component | Max points | Why this weight |
|-----------|-----------|-----------------|
| Genre match | 2.0 | Strongest single signal of taste |
| Energy proximity | 2.0 | The headline "feel" dimension |
| Mood match | 1.0 | Secondary label |
| Valence / danceability / acousticness / tempo | 1.0 each | Supporting texture |

Max possible score is **9.0**. `tempo_bpm` is min-max scaled with
`(bpm - 60) / (152 - 60)` before scoring so its large range does not dominate.

**Ranking:** sort songs by `total_score` (highest first), break ties, and return
the top *K*.

### Potential Biases

- **Over-prioritizing genre.** A genre match is worth a full 2.0 points, so the
  system may bury a song that perfectly matches the user's mood and energy just
  because it carries the "wrong" genre label (e.g. a mellow jazz track for a
  lofi fan). Great cross-genre matches can be ignored.
- **Redundant "calm vs. hyper" features.** `energy`, `acousticness`, and `tempo`
  tend to move together, so the score effectively counts that one axis three
  times — quieter, slower, acoustic songs get a structural advantage for a
  low-energy profile.
- **Popularity / catalog bias.** With only 20 songs and some genres represented
  by a single track, the "best" match is often just the least-bad option, and
  under-represented genres can never win unless the profile explicitly asks for
  them.
- **Cold-start narrowness.** The profile is a fixed set of targets, so the system
  keeps recommending the same "type" of song and never surfaces variety the user
  might actually enjoy.

---

## Define Your Data

My catalog lives in `data/songs.csv`. Each row is one song with these features:
`id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability,
acousticness`. Energy, valence, danceability, and acousticness are on a 0.0–1.0
scale, and tempo is in BPM.

The starter file gave me 10 songs, but the genres and moods were narrow (mostly
pop, lofi, and chill/happy variations). To make recommendations more interesting
and to stress-test my scoring rule against very different kinds of music, I used
my AI coding assistant to expand the catalog to 18 songs.

**Prompt I used:**

> Here are the headers and a few rows from my song catalog:
> `id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness`.
> Generate 8 additional songs as valid CSV rows using these exact headers and
> continuing the id numbering. Cover a diverse range of genres and moods that are
> NOT already in the file (e.g. classical, hip-hop, edm, country, r&b, reggae,
> metal, folk). Keep energy, valence, danceability, and acousticness between 0.0
> and 1.0, use a realistic tempo_bpm, and make each song's feature values
> coherent with its genre and mood (e.g. a classical melancholy track should have
> low energy, slow tempo, and high acousticness).

**Songs I added (ids 11–18):**

| id | genre | mood | why it adds diversity |
|----|-------|------|----------------------|
| 11 | classical | melancholy | very low energy, high acousticness — opposite end from the pop tracks |
| 12 | hip-hop | confident | high danceability with low acousticness |
| 13 | edm | euphoric | highest energy + danceability, near-zero acoustic |
| 14 | country | nostalgic | mid energy, acoustic-leaning |
| 15 | r&b | romantic | high valence, smooth mid-tempo |
| 16 | reggae | laid-back | high valence, groovy but relaxed |
| 17 | metal | aggressive | max energy, fastest tempo, low valence |
| 18 | folk | wistful | low energy, high acousticness |

Every added song introduces a genre **and** a mood not present in the starter
file, and I kept the feature values consistent with each style so the catalog
still makes musical sense.

I later added two more hip-hop tracks by J. Cole (ids 19–20, moods
`introspective` and `motivational`) to give the catalog some songs that share an
artist and genre but differ in energy and mood — useful for testing how the
recommender ranks similar-but-not-identical songs. The catalog now has 20 songs.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Running `python src/main.py` from the project root with the "chill lofi listener"
profile produces the following ranked output:

```
Loaded songs: 20

============================================================
  TOP RECOMMENDATIONS
  for a lofi / chill listener
============================================================

  #1  Midnight Coding  -  8.83 pts
      LoRoom  |  lofi / chill
      Reasons:
        - genre match: lofi (+2.0)
        - mood match: chill (+1.0)
        - energy close to target (0.42) (+1.96)
        - valence close to target (0.56) (+0.98)
        - danceability close to target (0.62) (+0.98)
        - acousticness close to target (0.71) (+0.91)
        - tempo_bpm close to target (78) (+1.00)

  #2  Library Rain  -  8.75 pts
      Paper Lanterns  |  lofi / chill
      Reasons:
        - genre match: lofi (+2.0)
        - mood match: chill (+1.0)
        - energy close to target (0.35) (+1.90)
        - valence close to target (0.6) (+0.98)
        - danceability close to target (0.58) (+0.98)
        - acousticness close to target (0.86) (+0.94)
        - tempo_bpm close to target (72) (+0.95)

  #3  Focus Flow  -  7.95 pts
      LoRoom  |  lofi / focused
      Reasons:
        - genre match: lofi (+2.0)
        - energy close to target (0.4) (+2.00)
        - valence close to target (0.59) (+0.99)
        - danceability close to target (0.6) (+1.00)
        - acousticness close to target (0.78) (+0.98)
        - tempo_bpm close to target (80) (+0.98)

  #4  Spacewalk Thoughts  -  6.22 pts
      Orbit Bloom  |  ambient / chill
      Reasons:
        - mood match: chill (+1.0)
        - energy close to target (0.28) (+1.76)
        - valence close to target (0.65) (+0.93)
        - danceability close to target (0.41) (+0.81)
        - acousticness close to target (0.92) (+0.88)
        - tempo_bpm close to target (60) (+0.84)

  #5  Coffee Shop Stories  -  5.55 pts
      Slow Stereo  |  jazz / relaxed
      Reasons:
        - energy close to target (0.37) (+1.94)
        - valence close to target (0.71) (+0.87)
        - danceability close to target (0.54) (+0.94)
        - acousticness close to target (0.89) (+0.91)
        - tempo_bpm close to target (90) (+0.89)

============================================================
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Stress Test: Diverse & Adversarial Profiles

To stress-test the scoring logic I defined a suite of user profiles in
`src/main.py` and ran the recommender against all of them (`python src/main.py`).
The suite has two groups:

1. **Three realistic, coherent listeners** — *High-Energy Pop*, *Chill Lofi*, and
   *Deep Intense Rock*.
2. **Five adversarial / edge-case profiles** — designed with an AI assistant to
   try to "trick" the scorer: conflicting preferences, impossible targets, an
   empty profile, out-of-range values, and a genre-only profile.

### Realistic Profile 1 — High-Energy Pop

```
============================================================
  TOP RECOMMENDATIONS - High-Energy Pop
  for a pop / happy listener
============================================================

  #1  Sunrise City  -  8.63 pts
      Neon Echo  |  pop / happy
      Reasons:
        - genre match: pop (+2.0)
        - mood match: happy (+1.0)
        - energy close to target (0.82) (+1.84)
        - valence close to target (0.84) (+0.99)
        - danceability close to target (0.79) (+0.94)
        - acousticness close to target (0.18) (+0.92)
        - tempo_bpm close to target (118) (+0.94)

  #2  Gym Hero  -  7.72 pts
      Max Pulse  |  pop / intense
      Reasons:
        - genre match: pop (+2.0)
        - energy close to target (0.93) (+1.94)
        - valence close to target (0.77) (+0.92)
        - danceability close to target (0.88) (+0.97)
        - acousticness close to target (0.05) (+0.95)
        - tempo_bpm close to target (132) (+0.94)

  #3  Rooftop Lights  -  6.39 pts
      Indigo Parade  |  indie pop / happy
      Reasons:
        - mood match: happy (+1.0)
        - energy close to target (0.76) (+1.72)
        - valence close to target (0.81) (+0.96)
        - danceability close to target (0.82) (+0.97)
        - acousticness close to target (0.35) (+0.75)
        - tempo_bpm close to target (124) (+0.99)

  #4  Neon Overdrive  -  5.70 pts
      Pulsewave  |  edm / euphoric
      Reasons:
        - energy close to target (0.95) (+1.90)
        - valence close to target (0.88) (+0.97)
        - danceability close to target (0.92) (+0.93)
        - acousticness close to target (0.03) (+0.93)
        - tempo_bpm close to target (128) (+0.97)

  #5  Concrete Kings  -  5.34 pts
      Prime Verse  |  hip-hop / confident
      Reasons:
        - energy close to target (0.85) (+1.90)
        - valence close to target (0.62) (+0.77)
        - danceability close to target (0.9) (+0.95)
        - acousticness close to target (0.08) (+0.98)
        - tempo_bpm close to target (96) (+0.74)

============================================================
```

*Reasonable:* the two `pop` songs top the list, and the genre-less-but-energetic
`edm`/`hip-hop` tracks follow — proximity is doing its job.

### Realistic Profile 2 — Chill Lofi

```
============================================================
  TOP RECOMMENDATIONS - Chill Lofi
  for a lofi / chill listener
============================================================

  #1  Midnight Coding  -  8.83 pts
      LoRoom  |  lofi / chill
      Reasons:
        - genre match: lofi (+2.0)
        - mood match: chill (+1.0)
        - energy close to target (0.42) (+1.96)
        - valence close to target (0.56) (+0.98)
        - danceability close to target (0.62) (+0.98)
        - acousticness close to target (0.71) (+0.91)
        - tempo_bpm close to target (78) (+1.00)

  #2  Library Rain  -  8.75 pts
      Paper Lanterns  |  lofi / chill
      Reasons:
        - genre match: lofi (+2.0)
        - mood match: chill (+1.0)
        - energy close to target (0.35) (+1.90)
        - valence close to target (0.6) (+0.98)
        - danceability close to target (0.58) (+0.98)
        - acousticness close to target (0.86) (+0.94)
        - tempo_bpm close to target (72) (+0.95)

  #3  Focus Flow  -  7.95 pts
      LoRoom  |  lofi / focused
      Reasons:
        - genre match: lofi (+2.0)
        - energy close to target (0.4) (+2.00)
        - valence close to target (0.59) (+0.99)
        - danceability close to target (0.6) (+1.00)
        - acousticness close to target (0.78) (+0.98)
        - tempo_bpm close to target (80) (+0.98)

  #4  Spacewalk Thoughts  -  6.22 pts
      Orbit Bloom  |  ambient / chill
      Reasons:
        - mood match: chill (+1.0)
        - energy close to target (0.28) (+1.76)
        - valence close to target (0.65) (+0.93)
        - danceability close to target (0.41) (+0.81)
        - acousticness close to target (0.92) (+0.88)
        - tempo_bpm close to target (60) (+0.84)

  #5  Coffee Shop Stories  -  5.55 pts
      Slow Stereo  |  jazz / relaxed
      Reasons:
        - energy close to target (0.37) (+1.94)
        - valence close to target (0.71) (+0.87)
        - danceability close to target (0.54) (+0.94)
        - acousticness close to target (0.89) (+0.91)
        - tempo_bpm close to target (90) (+0.89)

============================================================
```

### Realistic Profile 3 — Deep Intense Rock

```
============================================================
  TOP RECOMMENDATIONS - Deep Intense Rock
  for a rock / intense listener
============================================================

  #1  Storm Runner  -  8.87 pts
      Voltline  |  rock / intense
      Reasons:
        - genre match: rock (+2.0)
        - mood match: intense (+1.0)
        - energy close to target (0.91) (+1.98)
        - valence close to target (0.48) (+0.97)
        - danceability close to target (0.66) (+0.94)
        - acousticness close to target (0.1) (+1.00)
        - tempo_bpm close to target (152) (+0.98)

  #2  Gym Hero  -  6.17 pts
      Max Pulse  |  pop / intense
      Reasons:
        - mood match: intense (+1.0)
        - energy close to target (0.93) (+1.98)
        - valence close to target (0.77) (+0.68)
        - danceability close to target (0.88) (+0.72)
        - acousticness close to target (0.05) (+0.95)
        - tempo_bpm close to target (132) (+0.84)

  #3  Iron Verdict  -  5.49 pts
      Ashfall  |  metal / aggressive
      Reasons:
        - energy close to target (0.98) (+1.88)
        - valence close to target (0.35) (+0.90)
        - danceability close to target (0.55) (+0.95)
        - acousticness close to target (0.02) (+0.92)
        - tempo_bpm close to target (168) (+0.84)

  #4  Night Drive Loop  -  5.01 pts
      Neon Echo  |  synthwave / moody
      Reasons:
        - energy close to target (0.75) (+1.66)
        - valence close to target (0.49) (+0.96)
        - danceability close to target (0.73) (+0.87)
        - acousticness close to target (0.22) (+0.88)
        - tempo_bpm close to target (110) (+0.64)

  #5  Neon Overdrive  -  4.92 pts
      Pulsewave  |  edm / euphoric
      Reasons:
        - energy close to target (0.95) (+1.94)
        - valence close to target (0.88) (+0.57)
        - danceability close to target (0.92) (+0.68)
        - acousticness close to target (0.03) (+0.93)
        - tempo_bpm close to target (128) (+0.80)

============================================================
```

### Adversarial 1 — Conflicting: High-Energy but Sad & Acoustic

`energy: 0.95`, `mood: sad`, `valence: 0.10`, `acousticness: 0.95`. High energy
and high acousticness almost never co-occur, so no song can satisfy all of it.

```
============================================================
  TOP RECOMMENDATIONS - Conflicting: High-Energy but Sad & Acoustic
  for a any / sad listener
============================================================

  #1  Iron Verdict  -  3.69 pts
      Ashfall  |  metal / aggressive
      Reasons:
        - energy close to target (0.98) (+1.94)
        - valence close to target (0.35) (+0.75)
        - acousticness close to target (0.02) (+0.07)
        - tempo_bpm close to target (168) (+0.93)

  #2  Storm Runner  -  3.62 pts
      Voltline  |  rock / intense
      Reasons:
        - energy close to target (0.91) (+1.92)
        - valence close to target (0.48) (+0.62)
        - acousticness close to target (0.1) (+0.15)
        - tempo_bpm close to target (152) (+0.93)

  #3  Gym Hero  -  3.14 pts
      Max Pulse  |  pop / intense
      Reasons:
        - energy close to target (0.93) (+1.96)
        - valence close to target (0.77) (+0.33)
        - acousticness close to target (0.05) (+0.10)
        - tempo_bpm close to target (132) (+0.75)

  #4  Night Drive Loop  -  3.03 pts
      Neon Echo  |  synthwave / moody
      Reasons:
        - energy close to target (0.75) (+1.60)
        - valence close to target (0.49) (+0.61)
        - acousticness close to target (0.22) (+0.27)
        - tempo_bpm close to target (110) (+0.55)

  #5  Neon Overdrive  -  3.01 pts
      Pulsewave  |  edm / euphoric
      Reasons:
        - energy close to target (0.95) (+2.00)
        - valence close to target (0.88) (+0.22)
        - acousticness close to target (0.03) (+0.08)
        - tempo_bpm close to target (128) (+0.71)

============================================================
```

*What it reveals:* the `energy` weight (2.0) dominates, so the scorer resolves
the conflict by throwing out "sad & acoustic" and returning the loudest, most
un-acoustic tracks in the catalog — the exact opposite of the mood asked for.
No song even matched the `sad` mood, so that signal was silently ignored.

### Adversarial 2 — Impossible: Calm Acoustic EDM

Asks for the `edm`/`euphoric` label but with `energy: 0.05`, `danceability:
0.10`, `acousticness: 0.98`, `tempo: 60` — the opposite of every EDM track.

```
============================================================
  TOP RECOMMENDATIONS - Impossible: Calm Acoustic EDM
  for a edm / euphoric listener
============================================================

  #1  Velvet Midnight  -  5.30 pts
      Aria Voss  |  classical / melancholy
      Reasons:
        - energy close to target (0.22) (+1.66)
        - valence close to target (0.28) (+0.92)
        - danceability close to target (0.3) (+0.80)
        - acousticness close to target (0.95) (+0.97)
        - tempo_bpm close to target (66) (+0.95)

  #2  Spacewalk Thoughts  -  4.72 pts
      Orbit Bloom  |  ambient / chill
      Reasons:
        - energy close to target (0.28) (+1.54)
        - valence close to target (0.65) (+0.55)
        - danceability close to target (0.41) (+0.69)
        - acousticness close to target (0.92) (+0.94)
        - tempo_bpm close to target (60) (+1.00)

  #3  Paper Boats  -  4.58 pts
      Wren & Willow  |  folk / wistful
      Reasons:
        - energy close to target (0.33) (+1.44)
        - valence close to target (0.47) (+0.73)
        - danceability close to target (0.44) (+0.66)
        - acousticness close to target (0.88) (+0.90)
        - tempo_bpm close to target (76) (+0.85)

  #4  Library Rain  -  4.29 pts
      Paper Lanterns  |  lofi / chill
      Reasons:
        - energy close to target (0.35) (+1.40)
        - valence close to target (0.6) (+0.60)
        - danceability close to target (0.58) (+0.52)
        - acousticness close to target (0.86) (+0.88)
        - tempo_bpm close to target (72) (+0.89)

  #5  Neon Overdrive  -  4.13 pts
      Pulsewave  |  edm / euphoric
      Reasons:
        - genre match: edm (+2.0)
        - mood match: euphoric (+1.0)
        - energy close to target (0.95) (+0.20)
        - valence close to target (0.88) (+0.32)
        - danceability close to target (0.92) (+0.18)
        - acousticness close to target (0.03) (+0.05)
        - tempo_bpm close to target (128) (+0.38)

  #5 (note) the only real EDM track lands last despite the +3.0 genre+mood bonus
============================================================
```

*What it reveals:* the numeric proximity terms (max 6.0) out-vote the categorical
`edm`+`euphoric` bonus (+3.0). The actual EDM song scores lowest because its feel
is so far off, while a calm `classical` track wins. The system silently
prioritizes "feel" over the stated genre — arguably the *right* call, but worth
knowing.

### Adversarial 3 — Empty: No Preferences

An empty `{}` profile. Every song scores 0.0.

```
============================================================
  TOP RECOMMENDATIONS - Empty: No Preferences
  for a any / any listener
============================================================

  #1  Sunrise City  -  0.00 pts
      Neon Echo  |  pop / happy
      Reasons:
        - no strong matches

  #2  Midnight Coding  -  0.00 pts
      LoRoom  |  lofi / chill
      Reasons:
        - no strong matches

  #3  Storm Runner  -  0.00 pts
      Voltline  |  rock / intense
      Reasons:
        - no strong matches

  #4  Library Rain  -  0.00 pts
      Paper Lanterns  |  lofi / chill
      Reasons:
        - no strong matches

  #5  Gym Hero  -  0.00 pts
      Max Pulse  |  pop / intense
      Reasons:
        - no strong matches

============================================================
```

*What it reveals:* no crash — the scorer handles missing keys gracefully. But
with all-zero scores the "ranking" is just the catalog's original CSV order
(`sorted` is stable), so it silently defaults to a popularity/insertion bias.

### Adversarial 4 — Out-of-Range: Values Beyond 0-1

`energy: 2.5`, `valence: -1.0`, `acousticness: 5.0`, `tempo: 400` — far outside
the expected ranges.

```
============================================================
  TOP RECOMMENDATIONS - Out-of-Range: Values Beyond 0-1
  for a metal / any listener
============================================================

  #1  Iron Verdict  -  2.98 pts
      Ashfall  |  metal / aggressive
      Reasons:
        - genre match: metal (+2.0)
        - energy close to target (0.98) (+0.00)
        - valence close to target (0.35) (+0.00)
        - acousticness close to target (0.02) (+0.00)
        - tempo_bpm close to target (168) (+0.98)

  #2  Storm Runner  -  0.84 pts
      Voltline  |  rock / intense
      Reasons:
        - energy close to target (0.91) (+0.00)
        - valence close to target (0.48) (+0.00)
        - acousticness close to target (0.1) (+0.00)
        - tempo_bpm close to target (152) (+0.84)

  #3  Gym Hero  -  0.65 pts
      Max Pulse  |  pop / intense
      Reasons:
        - energy close to target (0.93) (+0.00)
        - valence close to target (0.77) (+0.00)
        - acousticness close to target (0.05) (+0.00)
        - tempo_bpm close to target (132) (+0.65)

  #4  Neon Overdrive  -  0.62 pts
      Pulsewave  |  edm / euphoric
      Reasons:
        - energy close to target (0.95) (+0.00)
        - valence close to target (0.88) (+0.00)
        - acousticness close to target (0.03) (+0.00)
        - tempo_bpm close to target (128) (+0.62)

  #5  Rooftop Lights  -  0.58 pts
      Indigo Parade  |  indie pop / happy
      Reasons:
        - energy close to target (0.76) (+0.00)
        - valence close to target (0.81) (+0.00)
        - acousticness close to target (0.35) (+0.00)
        - tempo_bpm close to target (124) (+0.58)

============================================================
```

*What it reveals:* the proximity formula `max(0, 1 - |value - target|)` clamps at
0, so out-of-range energy/valence/acousticness all collapse to +0.00 instead of
going negative — the scorer degrades safely. Only the min-max-clamped `tempo_bpm`
and the `metal` genre bonus still contribute, so ranking falls back to those.
Note the inputs are **never validated**; garbage just silently contributes zero.

### Adversarial 5 — Genre-Only: hip-hop and nothing else

A single categorical preference, no numeric targets.

```
============================================================
  TOP RECOMMENDATIONS - Genre-Only: hip-hop and nothing else
  for a hip-hop / any listener
============================================================

  #1  Concrete Kings  -  2.00 pts
      Prime Verse  |  hip-hop / confident
      Reasons:
        - genre match: hip-hop (+2.0)

  #2  Reflections in the Rain  -  2.00 pts
      J. Cole  |  hip-hop / introspective
      Reasons:
        - genre match: hip-hop (+2.0)

  #3  Crown Weight  -  2.00 pts
      J. Cole  |  hip-hop / motivational
      Reasons:
        - genre match: hip-hop (+2.0)

  #4  Sunrise City  -  0.00 pts
      Neon Echo  |  pop / happy
      Reasons:
        - no strong matches

  #5  Midnight Coding  -  0.00 pts
      LoRoom  |  lofi / chill
      Reasons:
        - no strong matches

============================================================
```

*What it reveals:* all three hip-hop tracks tie at exactly 2.00 with no
tie-breaker, so their relative order is just CSV order. The system has no way to
rank within a genre when the user gives no numeric signal.

---

## Experiments You Tried

### Experiment: Weight Shift — double energy, halve genre

**The change.** In `src/recommender.py` I temporarily changed two constants and
re-ran `python src/main.py`, then reverted them:

| Constant | Baseline | Experiment |
|----------|----------|------------|
| `GENRE_WEIGHT` | 2.0 | **1.0** (halved) |
| `NUMERIC_WEIGHTS["energy"]` | 2.0 | **4.0** (doubled) |

**Math sanity check.** The proximity term stays bounded 0.0–1.0, so energy now
contributes 0.0–4.0 and genre 0.0–1.0. Max possible score rises from **9.0 → 10.0**
(genre 1 + mood 1 + energy 4 + valence/dance/acoustic/tempo 1 each). Nothing can
go negative, so the ranking math stays valid — the change only *re-weights* the
same components.

**What happened — realistic profiles (top 5):**

| Rank | High-Energy Pop | Chill Lofi | Deep Intense Rock |
|------|-----------------|------------|-------------------|
| 1 | Sunrise City | Midnight Coding | Storm Runner |
| 2 | Gym Hero | Library Rain | Gym Hero |
| 3 | Rooftop Lights | Focus Flow | Iron Verdict |
| 4 | Neon Overdrive | Spacewalk Thoughts | **Neon Overdrive** ↑ (was Night Drive Loop) |
| 5 | Concrete Kings | Coffee Shop Stories | **Concrete Kings** (new; Neon Overdrive moved up) |

For **High-Energy Pop** and **Chill Lofi** the top 5 order was *identical* to
baseline — only the raw point totals grew. **Deep Intense Rock** was the only
realistic profile whose ranking changed, and only in the tail (#4–#5): halving
genre let the higher-*energy* `edm`/`hip-hop` tracks (Neon Overdrive 0.95, Concrete
Kings 0.85) overtake the lower-energy `synthwave` track Night Drive Loop (0.75).

**What happened — adversarial profiles:**

- *Impossible: Calm Acoustic EDM* — the one real **EDM** song (Neon Overdrive)
  **fell out of the top 5 entirely**. With genre worth only 1.0, its +1.0 genre
  bonus no longer offset its wildly wrong (high-energy) feel, and the doubled
  energy weight punished that mismatch even harder.
- *Conflicting: High-Energy but Sad & Acoustic* — same top 3, but the tail shifted
  toward the very highest-energy tracks (Neon Overdrive rose, Concrete Kings
  entered), reinforcing that "energy" now drives the bus.

**More accurate, or just different?**

Mostly **just different** — for coherent listeners whose genre and energy
preferences *agree*, the two signals reinforce each other, so re-weighting them
barely changed *what* got recommended (top 3 unchanged in all three cases); it
mainly inflated the scores. The change only *mattered* where genre and feel
**disagree**: cross-genre and adversarial cases. There it's a genuine trade-off,
not a clear improvement — it became **more faithful to the "feel"** the user
described but **less faithful to explicit genre requests** (an EDM search stopped
returning the EDM song). Which is "more accurate" depends on whether you trust the
user's stated genre or their stated vibe.

*The weights in `recommender.py` were reverted to baseline (genre 2.0, energy 2.0)
after recording these results.*

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



