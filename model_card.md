# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

It matches songs to the "vibe" a listener describes.

---

## 2. Intended Use  

**Goal / what it does.** VibeMatch suggests songs. You give it your taste, and it
returns the top 5 songs that fit best. It also explains *why* each song was picked.

**Who it's for.** This is a classroom project. It is built to learn how
recommenders work, not to run a real music app.

**What it assumes.** It assumes you can describe your taste as numbers and labels
(a genre, a mood, and how energetic/acoustic/danceable you want the music).

**What it should NOT be used for.** It should not be used for real listeners or
real products. It has only 20 songs, it does not learn from what you actually play,
and it does not know anything about lyrics, artists, or culture. Do not use it to
make real decisions about what people should hear.

---

## 3. How the Model Works  

Think of it like a checklist for every song.

For each song, VibeMatch asks: "How close is this song to what the user wants?"

- If the song's **genre** matches, it gets points. If the **mood** matches, it gets
  a few more.
- For numbers like **energy, happiness, danceability, how acoustic it is, and
  tempo**, it checks how *close* the song is to your target. Closer means more
  points. It rewards being close, not being high or low.
- It adds up all the points into one score.
- Then it sorts every song from highest score to lowest and shows you the top 5.

The key idea is **closeness**, not size. A song does not win for being the loudest
or the calmest — it wins for being nearest to *your* preferred setting.

**What I changed from the starter.** The starter just returned the first few songs
with no real scoring. I built the actual scoring rules (genre, mood, and the five
numeric closeness checks), scaled tempo so its big numbers don't drown out the
others, and added a plain-English reason for every recommendation.

---

## 4. Data  

- **Size:** 20 songs, stored in `data/songs.csv`.
- **Features per song:** title, artist, genre, mood, energy, tempo, valence
  (happiness), danceability, and acousticness. The last five are numbers; energy,
  valence, danceability, and acousticness sit between 0 and 1, and tempo is in BPM.
- **Genres/moods:** a wide spread — pop, lofi, rock, jazz, hip-hop, edm, classical,
  metal, folk, reggae, and more. Each song has its own mood label too.
- **What I changed:** the starter had 10 narrow songs. I used an AI assistant to add
  10 more across new genres and moods so the catalog could be stress-tested.
- **What's missing:** it is tiny. Most genres have only one song, so there isn't
  enough variety to give a genre fan a real list. It also has no lyrics, no
  language, no release year, and no real listening history — big parts of real
  musical taste are simply not in the data.

---

## 5. Strengths  

- **Clear, coherent users get great results.** For a "chill lofi" or "high-energy
  pop" listener, the top picks are exactly the songs a person would expect.
- **It explains itself.** Every recommendation comes with a reason line, so you can
  see *why* a song was chosen. That makes it easy to trust and easy to debug.
- **It captures "feel" well.** Because it rewards closeness, it correctly separates
  calm music from energetic music and can even find a good cross-genre match.
- **It fails gracefully.** Weird or impossible inputs (empty profiles, out-of-range
  numbers) don't crash it; it just returns the least-wrong answer.

---

## 6. Limitations and Bias 

The clearest weakness I found is an **energy "filter bubble" caused by
over-weighting a redundant signal.** `energy` is the heaviest numeric term in the
score (weight 2.0, tied with genre), but it also moves together with
`danceability`, `tempo`, and inversely with `acousticness` — so the scorer
effectively measures the same "calm-vs-hyper" axis three or four times and lets
the energy gap dominate everything else. In my experiments this meant the same
handful of loudest tracks (Neon Overdrive, Gym Hero, Iron Verdict) kept surfacing
in the top 5 across completely unrelated user profiles, while a genuinely
mid-energy song like Night Drive Loop (0.75) was structurally buried because it is
never closest to either extreme. It also lets energy silently override stated
mood: for a "high-energy but sad and acoustic" user the +2.0 energy term alone
decided the winner and the requested sad/acoustic feel was discarded entirely.
This unfairly favors users with extreme-energy tastes (very loud or very quiet)
and gives worse, more repetitive recommendations to anyone whose taste sits in the
middle or who cares more about mood than intensity.

Secondary limitations: 12 of 15 genres have only one song, so under-represented
genres can never form a diverse top 5; and empty or tied profiles fall back to the
CSV's original row order, a hidden position bias with no real tie-breaker.

---

## 7. Evaluation  

**How I tested it.** I built eight user profiles in `src/main.py` and ran them all
at once. Three were "realistic" listeners — **High-Energy Pop**, **Chill Lofi**,
and **Deep Intense Rock** — and five were "adversarial" edge cases meant to try to
break the logic: a **Conflicting** user (wants loud *and* sad *and* acoustic), an
**Impossible** user (wants calm, slow, acoustic "EDM"), an **Empty** user with no
preferences, an **Out-of-Range** user with nonsense values, and a **Genre-Only**
user. For each one I looked at the top 5 songs and read the "reasons" line to check
the system was recommending things for sensible reasons, not by accident.

**What surprised me.** Two things. First, the *same loud songs kept reappearing*
for very different people — a track like Gym Hero showed up for the pop fan, the
rock fan, and the conflicting user. Second, when a user asked for something
impossible, the system didn't complain or return nothing; it quietly gave them the
"least wrong" answer, sometimes ignoring the part of their request it couldn't
satisfy (the sad/acoustic user got the loudest metal track in the catalog).

**Why does "Gym Hero" keep showing up for a "Happy Pop" fan?** (Plain-language
version.) Gym Hero is filed under *pop* and it's extremely upbeat, fast, and
danceable — the numbers that describe it look almost exactly like what a
high-energy pop fan asked for. The only thing "wrong" with it is that its mood is
labeled *intense* instead of *happy*. But the mood label is only one small point
out of nine, while matching the genre and the high-energy "feel" is worth a lot
more. So the system decides that a song which *sounds* like happy pop is a great
pick even if a human tagged its mood differently. In short: it trusts the
measurable vibe of the song over the one-word mood sticker.

**Profile-by-profile comparisons:**

- **High-Energy Pop vs. Chill Lofi** — These are opposites and the results proved
  it: the pop fan got bright, loud, danceable tracks (Sunrise City, Gym Hero)
  while the lofi fan got quiet, acoustic, slow ones (Midnight Coding, Library
  Rain). There was zero overlap, which is exactly what you'd want — the two
  profiles are clearly testing opposite ends of the "energy" dial.

- **High-Energy Pop vs. Deep Intense Rock** — Both want *loud* music, so they
  overlapped: Gym Hero and Neon Overdrive appeared for both. The difference is
  brightness — pop pulled cheerful, high-valence songs to the top, while rock
  pulled darker, more aggressive ones (Iron Verdict, Night Drive Loop). This makes
  sense: they agree on energy but disagree on mood/valence, so the shared loud
  songs rank for both, and the "happy vs. dark" tracks split them apart.

- **Chill Lofi vs. Deep Intense Rock** — Complete opposites again, and no shared
  songs. Lofi wants soft and acoustic; rock wants loud and driving. A clean
  confirmation that the energy and acousticness targets actually steer the list.

- **Conflicting vs. Impossible** — Both are "no song can satisfy this" profiles,
  but the system resolved them differently. The Conflicting user (loud + sad +
  acoustic) got the *loudest* songs because energy is the heaviest signal, so
  "loud" won and "sad/acoustic" was dropped. The Impossible user (calm acoustic
  "EDM") got the *calmest, most acoustic* songs — a classical track won — because
  there were four numeric "calm" clues that together outvoted the single "EDM"
  label. Same kind of contradiction, opposite resolution, depending on which side
  had more numeric weight behind it.

- **Empty vs. Genre-Only** — The Empty user (no preferences) scored every song 0.0
  and just got the catalog in its original order — a reminder that with no
  information the system has no real opinion. The Genre-Only user (hip-hop, nothing
  else) got all three hip-hop songs tied at the exact same score, then padded with
  0.0 songs. Comparing the two shows the system needs *numeric* preferences to rank
  within a genre; a genre label alone can find the right family of songs but can't
  order them.

**Cross-comparisons (realistic vs. adversarial):** these are the pairs that
explain *why the same songs keep recurring*.

- **High-Energy Pop vs. Conflicting** — Even though the Conflicting user asked for
  *sad and acoustic*, both lists surfaced Gym Hero and Neon Overdrive. That's the
  clearest proof of the "loud songs recur" pattern: because both profiles ask for
  high energy, and energy is the heaviest signal, the loudest tracks bubble up for
  both — the pop fan *and* the person who explicitly wanted something sad.

- **Chill Lofi vs. Impossible** — The Impossible "calm acoustic EDM" user ended up
  with almost the same soft, acoustic songs as the Chill Lofi fan (Spacewalk
  Thoughts, Library Rain both appear). It makes sense: strip away the unrealistic
  "EDM" label and what's left is a request for quiet, acoustic music — so the
  system correctly lands the two very-different-sounding *requests* on the same
  calm shelf of the catalog.

- **Deep Intense Rock vs. Conflicting** — Heavy overlap at the top (Iron Verdict,
  Storm Runner, Gym Hero) because both want maximum energy. The rock fan gets them
  legitimately; the conflicting user gets them as a "least wrong" answer. Same
  songs, very different reasons — which is exactly the fairness concern from the
  Limitations section: a middle-of-the-road or mood-first listener would keep
  seeing this same loud cluster.

---

## 8. Future Work  

If I kept building this, I would change three things:

1. **Fix the energy over-weighting.** Energy counts too much and overlaps with
   tempo and acousticness. I'd lower its weight (or combine the overlapping
   features into one "calmness" score) so the same loud songs stop dominating.
2. **Add diversity to the top 5.** Right now the list can be five near-identical
   songs. I'd make it avoid repeats — for example, not showing three tracks by the
   same artist or the same sub-vibe in a row.
3. **Grow the catalog and add a tie-breaker.** With only 20 songs, most genres have
   one option. A bigger catalog plus a real tie-breaker (instead of falling back to
   file order) would make within-genre ranking meaningful.

---

## 9. Personal Reflection  

**My biggest learning moment.** It was watching the weight experiment. When I
doubled energy and halved genre, the top 3 songs for my normal listeners barely
moved — but the adversarial users flipped, and an actual EDM song fell out of an
EDM search. That was the moment recommenders stopped feeling magical. I realized
the "smart" behavior is really just a pile of small weighted numbers, and whoever
sets those weights quietly decides what people get to hear.

**How AI tools helped, and when I double-checked them.** The AI assistant was
great for speed — it helped me brainstorm the adversarial profiles (like the
"loud but sad and acoustic" user), expand the song catalog, and explain why a
given song ranked first. But I learned not to trust it blindly. When it changed
the weights, I checked the math myself to make sure the max score and the
proximity formula still made sense. I also caught small real-world issues it
missed, like an em-dash printing as a broken character in the Windows terminal.
The pattern that worked was: let the AI draft and explain, but verify anything
that touches the actual scoring or the output.

**What surprised me about simple algorithms.** There's no machine learning here at
all — just addition and "how close is this number to that number." Yet the output
genuinely *feels* like a recommendation. Reading the reason lines, it almost seems
like the system "gets" you. That gap between how simple the code is and how smart
the result feels was the most eye-opening part, and it made me more skeptical of
apps that present their picks as if they truly understand us.

**What I'd try next.** I'd fix the energy over-weighting so the same loud songs
stop dominating, add a diversity rule so the top 5 aren't near-duplicates, and grow
the catalog with a real tie-breaker. Longer term, I'd love to feed it real
listening history instead of a hand-typed profile and see how much better — or how
much more biased — it gets.

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
