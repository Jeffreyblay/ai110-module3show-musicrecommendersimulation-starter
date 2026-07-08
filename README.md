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

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

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



