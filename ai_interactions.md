# AI Interactions Log

This log documents how I used an AI coding assistant (Claude) to complete the
four stretch challenges for the Music Recommender Simulation. Each section
records the prompt(s) I gave, a summary of what the AI produced, and my own
manual verification notes.

---

## Challenge 1 — Advanced Song Features (SF8: Agentic Workflow)

**What task did I give the agent?**

Add five or more complex attributes to the dataset that were not in the
baseline, and make the scoring logic actually use them.

**Prompt used:**

> "Add 5+ advanced attributes to `data/songs.csv` (e.g. song popularity 0-100,
> release decade, detailed mood tags). Update `load_songs` and the scoring
> logic in `src/recommender.py` so scoring accounts for the new attributes.
> Keep the existing tests passing — don't break the `Song`/`UserProfile`
> dataclasses that `tests/test_recommender.py` depends on."

**What did the agent generate or change?**

Five new attributes were added to every row of `data/songs.csv`:

1. `instrumentalness` (0.0–1.0) — vocal vs. instrumental
2. `popularity` (0–100) — niche vs. chart-topping
3. `release_year` (int) — used to derive a `release_decade` label (e.g. "2020s")
4. `language` (e.g. "en", "instrumental")
5. `mood_tags` — detailed descriptors stored pipe-separated in one cell
   (e.g. `euphoric|uplifting|summery`) so they don't collide with the CSV commas

Code changes in `src/recommender.py`:
- `load_songs` now parses the new numeric columns, splits `mood_tags` on `|`,
  and derives `release_decade` from `release_year`.
- Scoring rewards a decade match, a language match, popularity proximity
  (min-max scaled 0–100 → 0–1), instrumentalness proximity, and the *overlap*
  between the user's preferred tags and the song's tags.
- The `Song` and `UserProfile` dataclasses gained the new fields **with
  defaults / `None`**, so the existing tests that build objects with only the
  original nine fields still construct correctly.

**What did I verify or fix manually?**

- Ran `python -m pytest -q` → 2 passed. The defaulted dataclass fields were the
  key detail; without defaults the tests would have failed on construction.
- Confirmed popularity is *scaled* before proximity — otherwise its 0–100 range
  would have swamped every 0–1 feature. I checked the "High-Energy Pop" profile
  and saw popularity contribute a sane `+0.93`, in line with the other features.
- Checked the mood-tags overlap is normalised by the number of tags the user
  asked for, so asking for more tags doesn't inflate scores unboundedly.

---

## Challenge 2 — Multiple Scoring Modes (SF10: Design Pattern)

**Which design pattern did I use?**

The **Strategy pattern**.

**How did AI help me brainstorm or implement it?**

I attached `recommender.py` and asked the assistant's chat:

> "I want two or more ranking strategies (Genre-First, Mood-First,
> Energy-Focused) that a user can switch between in `main.py`. Suggest a design
> pattern that keeps this modular so I'm not copy-pasting the scoring function
> per mode."

The AI weighed a few options and recommended Strategy over the alternatives:
- A big `if mode == ...` block inside `score_song` — rejected: adding a mode
  means editing the core function, and the branches duplicate logic.
- A separate scoring function per mode — rejected: the ranking logic would be
  copy-pasted three times and drift out of sync.
- **Strategy pattern** — chosen: one shared `score()` method lives on a base
  `ScoringStrategy`, and each mode is a subclass that only overrides a handful
  of weight attributes. One source of truth for the algorithm, trivial to add
  a new mode.

**How does the pattern appear in the final code?**

In `src/recommender.py`:
- `ScoringStrategy` — base class with the shared `score()` method and default
  weights.
- `GenreFirstStrategy`, `MoodFirstStrategy`, `EnergyFocusedStrategy` — subclasses
  overriding just the weights that define each mode.
- `STRATEGIES` registry + `get_strategy(name)` let `main.py` resolve a mode by
  name. `score_song` / `recommend_songs` accept a `strategy=` argument.

In `src/main.py`, running `python src/main.py Mood-First` runs a single mode;
with no argument it runs every mode so you can compare rankings side by side.

**What did I verify manually?**

Ran each mode and confirmed the rankings actually differ, e.g. Genre-First
pushes same-genre songs to the top while Energy-Focused reorders around tempo
and energy even when the genre doesn't match.

---

## Challenge 3 — Diversity and Fairness Logic

**Prompt used:**

> "Add a diversity penalty to the recommender: penalise a song's score if its
> artist (or genre) is already present in the top recommendations chosen so
> far, so one artist/genre can't dominate the top results. Explain the rule you
> implement."

**Rule the AI implemented:**

Instead of a plain sort-and-slice, `recommend_songs` now selects the top *k*
**greedily, one at a time**. Before each pick it subtracts
`diversity_penalty × (times the artist already appears + times the genre already
appears)` from every remaining candidate's base score, then takes the highest
*adjusted* score. A strong enough song can still win despite the penalty, but
repeats are pushed down. The penalty amount is a per-strategy attribute
(`diversity_penalty`, default `1.25`), and the applied penalty is shown in the
song's reasons for transparency.

**What did I verify manually?**

The "Genre-Only: hip-hop" profile is the clearest test — the catalog has three
hip-hop songs, two by J. Cole. Without the penalty the top three would all be
hip-hop. With it, only the first hip-hop song ranks near the top; the second is
penalised once (genre repeat) and the third, by an already-seen artist *and*
genre, is pushed below neutral songs. Confirmed via
`python src/main.py Balanced --plain`.

---

## Challenge 4 — Visual Summary Table

**Prompt used:**

> "Improve the terminal output with a formatted table for the top
> recommendations. The table MUST include the reasons for each score. Suggest
> using `tabulate` or ASCII formatting, and make it still run if `tabulate`
> isn't installed."

**What the AI produced:**

`format_recommendations_table` in `src/main.py` builds rows with columns
`# | Title | Artist | Genre / Mood | Score | Reasons`, where each reason sits on
its own line inside the cell. It uses `tabulate` (added to `requirements.txt`)
when available, and otherwise falls back to a dependency-free `_ascii_table`
that draws the same kind of grid with per-cell word wrapping. The original
nested-bullet layout is preserved behind a `--plain` flag.

**What did I verify manually?**

`tabulate` is not installed in my environment, so I confirmed the **fallback**
path renders a clean aligned grid with the reasons wrapped inside the Reasons
column. Both `python src/main.py` (table) and `python src/main.py --plain`
(bullets) run without errors.

---

## Overall verification

- `python -m pytest -q` → **16 passed** (2 original tests + 14 new in
  `tests/test_advanced.py` covering the advanced attributes, the scoring modes,
  the diversity penalty, and the OOP wrapper).
- `python src/main.py` runs all four scoring modes end to end against the
  realistic and adversarial profiles without errors.

Two of the new tests initially failed and were worth keeping honest about:
one assumed mood-tag scores grow with the raw number of shared tags, but the
design (correctly) normalises by how many tags the user asked for; the other
expected a diversity penalty in the reasons when the penalty had actually done
its job and *excluded* the repeated songs from the top results. Both tests were
corrected to match the real, intended behaviour rather than changing the code.
