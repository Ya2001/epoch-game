# Epoch — Game Design Document

*Working title. Alternatives to consider: **Anno**, **Chronicle**, **Timefold**, **Yearwise**, **Atlas Chronicle**.*

---

## 1. Concept in one sentence

You are given a single historical event. Drag a year slider from 1000 to 2026 to guess when it happened — and if you're stuck, spin the world map to see what else was going on elsewhere, because history is a web, not a line.

That last idea is the soul of the game. The hint system isn't a Google-lookup crutch; it's a mechanic that teaches you history is synchronous. When you learn that Gutenberg's press (1440) ran during the late Ming dynasty, or that Mozart died the year Haitian slaves revolted (1791), the hints become the point. The year-guess is just the scoring surface.

---

## 2. Why this has legs

Three games have proven this space works: Wordle (daily ritual + share-a-score), GeoGuessr (map exploration as play), and Timeguessr (image-based year guessing). None of them teach the *synchronicity* of world history. Epoch's zoom-based world-map hint system is the differentiating mechanic — nobody else has it, and it's the part that will get shared.

---

## 3. Core game loop

A round is roughly 30–60 seconds:

1. **Prompt** appears at the top: one event, one country of origin, no year.
2. **Player drags the slider.** As they drag, the world map underneath reacts — colors shift, little icons appear and fade, continents glow where the game knows "something noteworthy" happened near the selected year. This is ambient, not informational; it makes the year feel *alive*.
3. **Player zooms the map** if they want hints. Pinch (or tap) to zoom in on a continent, then a country. Tapping a country reveals one hint event from that place within ±10 years of the slider's current position. Hints cost points.
4. **Player locks in** their guess.
5. **Reveal.** The slider snaps to the actual year with a satisfying animation, error distance is shown, score is tallied, and a one-sentence "what else happened that year" epilogue runs across the screen — free learning, every single round.

The round has a strong rhythm: prompt → explore → commit → reveal → breath. That last "breath" moment — the epilogue — is what will make Epoch feel different from a quiz.

---

## 4. Game modes

You chose daily + endless. Here's how they differ and why both matter.

**Daily Chronicle.** One hand-picked event each day, same for every player worldwide, resets at midnight local. Three hint slots, scored against a global leaderboard, shareable as an emoji grid (copying Wordle's share grammar). This is the retention engine — the thing that builds the 30-day habit.

**Endless Run.** Unlimited rounds, procedurally sampled from the event library with difficulty scaling. You start with 3 lives; any guess more than 50 years off costs a life; any bullseye (within 2 years) grants a "time crystal" you can spend on a free hint. Ends when lives run out. This is the skill expression mode — the thing people play on a bus after the daily is done.

A third mode worth earmarking for later: **Era Campaign** — unlock themed decks (Medieval, Enlightenment, 20th Century, Modern) by hitting accuracy targets. Good content-driven retention, but don't build it until daily + endless are ironed out.

---

## 5. Scoring

Scoring should reward precision but not be cruel. A good curve:

Base score per round is 1000. Subtract the absolute year error — but not linearly, because the difference between "off by 1 year" and "off by 3 years" should feel dramatic, while "off by 40" and "off by 60" shouldn't. Use a curve like `score = round(1000 * exp(-error / 25))`. That gives a bullseye at 1000, a 10-year miss at ~670, a 25-year miss at ~368, a 50-year miss at ~135, and a century miss at ~18. Feels punishing at scale but generous when you're close.

Hints deduct a flat 150 points each; the third hint deducts 300. That way using one hint is fine, two is a choice, three is desperation.

Daily mode posts your raw score. Endless mode tracks longest streak (consecutive rounds within 15 years) as the headline stat.

---

## 6. The hint system — zoom-based

You picked zoom-based, which is the most ambitious option and also the most distinctive. Here's the model.

The map has three zoom levels. **Level 0 (globe):** six continent blobs, each pulsing with an intensity color keyed to "how many events are in the library for this continent within ±15 years of the slider." This is free atmosphere — no cost, just world-state visualization. **Level 1 (continent):** tap a continent to zoom. You see country regions and a small number of "event dots" glowing in countries that have hints available for the currently selected year. **Level 2 (country):** tap a country to reveal one hint event card — "In [country], [year-relative phrasing]: [event]." First hint shown = the ±3 year neighborhood; second pull from the same country = wider ±10 neighborhood.

A subtle but important design choice: hints should *always* use phrasing that anchors time relative to the slider, not absolute. So instead of "1492: Columbus voyages," you see "Around the same time as your current guess, sailors from Spain make their first Atlantic crossing." That preserves the puzzle and teaches synchronicity.

Two zoom gestures to support: pinch-out (phone default) and double-tap to zoom in one level. A dedicated back-arrow bubble in the corner zooms out one level — never trap the player in a zoom state.

---

## 7. Data model

The library is keyed on `(year, country)` but enriched to make sampling and hint generation fast.

```json
{
  "id": "evt_1440_de_gutenberg",
  "year": 1440,
  "country": "DE",
  "continent": "EU",
  "title": "Gutenberg's printing press",
  "prompt": "Movable-type printing begins revolutionizing European text reproduction.",
  "hint_short": "A goldsmith in Mainz perfects movable type.",
  "epilogue": "The same decade the Inca built Machu Picchu.",
  "difficulty": 2,
  "tags": ["technology", "europe", "renaissance"],
  "image": null
}
```

Fields and why:

The `id` is slug-style and deterministic so you can reference events stably across versions. The `country` uses ISO 3166-1 alpha-2 — lightweight, universal. The `continent` is denormalized for fast filtering at zoom level 0 (avoids a join or lookup on every slider tick). `prompt` is the full text shown as the riddle; `hint_short` is the terser version used in hint cards and should *never* contain the year. `epilogue` runs on reveal and should always pair the event with something from the *same* ±5 years on another continent — it's the magic moment, worth the content work. `difficulty` 1–5 drives endless-mode sampling. `tags` let you build era decks later.

**Sampling for hints at runtime.** Index events into two structures on load: a `byYear` sparse map (`{year: [id, ...]}`) and a `byCountry` map (`{country: [id, ...]}`). Given the current slider year `y` and a tapped country `c`, pull events from `byCountry[c]` where `|event.year - y| <= 10`, sort by proximity, return the closest one not yet shown this round. O(n) in events-per-country, which is small.

**Content scale to launch:** 365 events for daily-mode (one year of content, handpicked and curated), plus ~500 additional events for endless variety. Roughly 100 per continent is a healthy minimum for the zoom-hint mechanic to feel rich. Plan for a content editor (a simple spreadsheet → JSON pipeline) early — you'll be adding events forever.

---

## 8. Screen anatomy

A single-screen game, top to bottom, on a phone held in portrait.

The **top band** shows the prompt — one short sentence with the originating country named. No date, no giveaway words. Below it, a thin progress indicator if in endless mode.

The **middle band** is the world map. It fills most of the screen. Animation on this panel is the whole visual identity. When the slider moves, tiny ornaments fade in and out — a sail on the Atlantic during the Age of Exploration, a locomotive chugging through central Europe around 1830, a rocket near Florida around 1969. These are ambient and optional; they don't gate gameplay, but they're the "oh, nice" moments that make the game feel alive. Continents subtly shift hue with the era: deep indigo for medieval, warmer sienna for Renaissance, steely blue for industrial, bright sodium for modern.

The **bottom band** is the year slider. Oversized, rubber-band physics, with a big year readout that counts up/down with a tasteful odometer animation. Beside the slider sit two buttons: a hint indicator (showing hints-used and slots-remaining) and a lock-in button that transforms into the reveal button once pressed.

A **mode toggle** lives at the top corner — daily vs endless — and is visible only on the home screen, not during a round.

---

## 9. Animation language

Everything in Epoch should feel like it has mass but no friction. Three rules:

First, the slider is the pacemaker. Every animation tied to the slider should complete within one frame of the slider settling, or drift smoothly over 300ms if it's ambient. Never let the slider outrun its world — it breaks the sense of causality.

Second, zoom transitions are the signature move. Use a single smooth camera transform rather than cross-fades. Target 400ms cubic-bezier ease-out for a zoom in, 300ms for a zoom out (zooming out should feel *snappier* because the player wants escape). This is the gesture users will demo to friends.

Third, reveal animations deserve disproportionate polish. When the true year is revealed, the slider shouldn't just jump; it should accelerate, overshoot, settle. The error delta should count up with digits flipping. This is the six seconds of your game that go on social media.

Micro-stuff: haptics on slider tick at every decade boundary, on hint reveal, on lock-in, on bullseye. Sparingly.

---

## 10. Art direction

A "scholarly but modern" feel. Think Apple Maps x Moleskine x a quiet science-documentary. Dark background as default (indigo-black, #0b1020 base) with a warm-cream accent (#f5ecd4) for type. Continents as soft, slightly textured blobs — not geographically perfect, stylized and friendly. Country lines emerge only at zoom level 1.

Typography: a humanist sans for UI (Inter works, or IBM Plex Sans), a serif with small caps for the event prompts (EB Garamond, Cormorant) to give prompts a "dispatch from a library" voice. Numbers in the year readout: a tabular slab or display serif — something that feels historical and monumental.

Limit the palette. Two accent colors (one warm, one cool), one gold for bullseye/celebration, one red reserved *only* for hint depletion and lost lives. If everything glows, nothing does.

---

## 11. Technical stack

For mobile web (your call, and the right call for validation), the simplest credible stack:

Vanilla HTML + CSS + JS, or a tiny framework like Preact if you want components. No heavy framework overhead — this game should load in under 200ms on 4G. SVG for the map (better gesture handling and crisp zoom than Canvas for this use case). Use CSS transforms for the zoom camera and CSS custom properties keyed to the slider value for synchronized ambient animations — this lets you drive dozens of independent ambient effects off a single JS variable, which is what you want for "snappy, lots happening" without frame drops.

For the map geometry, two options. A **stylized simplified SVG** of continents you draw yourself (faster, more on-brand, less accurate) or a **TopoJSON world atlas** + d3-geo (accurate, heavier, uglier without styling work). Start with stylized. The game isn't a geography test; it's a history game that happens to use a map.

Data ships as a static JSON bundle — no backend for v0. When you need a backend (leaderboards, daily-event rotation), Cloudflare Workers + D1 is the cheapest credible option and keeps you inside one ecosystem.

Packaging: ship as a PWA so users can "add to home screen." This gets you 90% of the feel of a native app without App Store review, and you can always wrap it in Capacitor later if you want to pursue an app-store presence.

---

## 12. Content strategy

Content is the moat. Three principles.

**Curate, don't scrape.** Events pulled from Wikipedia by machine read as dry and culturally lopsided. Events written by a historian friend read as story. Budget at least 2 minutes of human writing per event. 365 events = about 12 hours of writing work, which is real but one-shot.

**Over-represent non-Western history.** The global default is Eurocentric; a game about world synchronicity shouldn't repeat that. Target at least 35% of events from Asia, Africa, and the Americas (pre- and post-colonial) across the timeline. This will also differentiate Epoch reviews.

**The epilogue is where you earn repeat play.** Every event needs a *paired* fact — something happening in a totally different part of the world in the same ±5 years. Not an easy task to write 365 of these, but this is the one piece of content I'd prioritize most, because it's the thing players will repeat-tell their friends.

---

## 13. Monetization (optional, later)

The game works fine as a free no-ad product if it's just your project. If you want it to pay for itself, the natural model is: Daily mode + first ~20 events of endless are free; unlocking the full endless library is a one-time $3.99 purchase; era campaigns are $1.99 each. Subscription is wrong for this game — it's a ritual you play for three minutes a day, not a service.

Don't monetize hints. That destroys the educational spine of the game.

---

## 14. Roadmap

*Week 1.* Lock the GDD (this document), write the first 50 events, build the prototype (done — see the HTML file shipped alongside this doc). Prove the core loop is fun in informal testing with 3–5 people.

*Weeks 2–4.* Expand to 200 curated events. Build the real zoom-based hint system with proper country polygons. Add scoring, lives, streak tracking. Implement PWA shell + local storage for daily-run state.

*Weeks 5–6.* Daily-event cycling via a tiny backend (Cloudflare Workers + a JSON file per day). Global leaderboard. Share-card generation.

*Weeks 7–8.* Polish pass: art, animation, haptics, sound (optional, light ambient). Soft-launch to a small testflight-style group, TestFlight for iOS via Capacitor wrap, APK for Android.

*Week 9+.* Content expansion to 500+, era campaigns, friends leaderboards. Only build these once DAU retention past day 7 is looking real.

---

## 15. Open questions for you

A few decisions I didn't make for you — worth thinking about before week 2:

On the year range: do you want 1000–2026 always, or do you want the slider range to *narrow* for some rounds (e.g., a "20th century only" daily)? Narrowing reduces the guessing space and could be a difficulty lever.

On hints from the same country: should a player be able to "exhaust" a country's hints within a round (forcing them to explore), or should hints pull infinitely? I'd lean toward exhausting — it forces map exploration, which is the mechanic you're paying for.

On reveal art: the epilogue is strongest as text, but a sparse illustration (one-line drawing of the event) would deepen it. Worth prototyping once the game loop is proven.

On visual style for the map: stylized blobs (recommended) or geographically accurate (more intimidating to build, less playful)?

On name: Epoch is fine as a working title. "Anno" might be stronger but is taken by Ubisoft's franchise. "Chronicle" is descriptive but crowded. "Timefold" has a nice origami connotation matching the paper-scholarly aesthetic. This deserves a real naming exercise before you ship.

---

## Appendix A — Example event records

```json
[
  {
    "id": "evt_1066_gb_hastings",
    "year": 1066, "country": "GB", "continent": "EU",
    "title": "Battle of Hastings",
    "prompt": "A Norman duke crosses the Channel and changes the English language forever.",
    "hint_short": "A French-speaking invader conquers the English throne.",
    "epilogue": "In the same years, the Seljuk Turks pushed into Anatolia, reshaping the Middle East."
  },
  {
    "id": "evt_1492_es_columbus",
    "year": 1492, "country": "ES", "continent": "EU",
    "title": "Columbus reaches the Americas",
    "prompt": "A Genoese sailor under Spanish funding makes an Atlantic crossing.",
    "hint_short": "Spain finishes the Reconquista and dispatches ships west.",
    "epilogue": "The same year, Spain expelled its Jewish population; Leonardo was sketching flying machines in Milan."
  },
  {
    "id": "evt_1969_us_moon",
    "year": 1969, "country": "US", "continent": "NA",
    "title": "Apollo 11 lands on the Moon",
    "prompt": "Humans walk on another world for the first time.",
    "hint_short": "A space agency in Florida fulfills a decade-old promise.",
    "epilogue": "That summer, half a million people attended Woodstock; the ARPANET went live; Muammar Gaddafi took power in Libya."
  }
]
```

## Appendix B — Event coverage targets

To keep the zoom hint system feeling rich, the library should have no fewer than these counts per continent by beta:

Europe 150, Asia 150, Africa 100, North America 100, South America 70, Oceania 50, Middle East (treated as its own region for hint diversity) 80. Total ~700 events. Roughly 50 per century across the 1000-year range keeps any slider position within a hint-productive neighborhood.
