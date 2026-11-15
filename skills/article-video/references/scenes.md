# scenes.json reference

A scenes file is `{"title": ..., "source": ..., "scenes": [ ... ]}`. Each scene has a `type`, its
on-screen content, and a `narration` string (the draft script for that scene). The narration drives
draft timing (about 2.5 words per second) until a recording exists; after recording, the transcript
of the chosen take replaces it for timing.

## Cues

Any revealable element can carry `"cue": "a phrase from the narration"`. The element fades in at the
moment that phrase is spoken (matched fuzzily against the transcript, so small wording changes in the
recording are fine). Pick 2–5 distinctive words that open the idea the element shows. Elements
without a cue are staggered after the previous one; a scene with no cues spreads its elements across
the narration. Headings and icons normally need no cue — they appear at the start of the scene.

## Scene types

| type | use for | fields |
|---|---|---|
| `title` | opening card | `title`, `subtitle`, `byline`, optional `icon` |
| `statement` | a thesis or a short sequence of claims | optional `heading`, optional `icon`, `lines[]`: `{text, style, tone?, gap?, cue}` |
| `compare` | A → B contrast or progression | `heading`, `items[2]`: `{icon, title, body, tone?, cue}`, `arrow` (default true), `footer {text, cue}` |
| `cards` | a framework of 2–4 categories | `heading`, `items[]`: `{icon, title, body, tone, strike?, strike_cue?, cue}`, `footer {text, cue}` |
| `list` | examples, especially things to retire | `heading`, `items[]`: `{text, cue}` (≤5), optional `strike {cue}` (strikes all items), `footer[]`: `{text, cue}` |
| `numbered` | 2–3 risks, lessons or steps with consequences | `heading`, `items[]`: `{title, body, result, cue, result_cue}` |
| `pills` | keep vs. change, with 2–4 takeaway words | `heading`, `left {title, body, tone, cue}`, `right {...}`, `pills[]`: `{text, cue}` |
| `closer` | the aphorism / closing line | optional `icons[]` (name or `{icon, strike: true}`), `lines[]`: `{text, tone, cue}` (1–3), `footer` (source or link) |

**Line styles** (`statement`): `body` (plain), `emph` (large teal serif — the key phrase), `accent`
(amber serif), `warn` (red italic — a turn or consequence), `quote` (italic), `small` (muted).
`gap` sets space after a line in line-heights (default 0.45; use 0.1 to tie two lines together).

**Tones**: `good` (teal), `bad` (red), `accent` (amber), `neutral` (ink).

**Icons**: `pencil`, `calculator`, `slide_rule` (wide; animates), `book`, `lightbulb`, `gear`,
`check`, `cross`. Icons are optional — most articles won't have a natural object metaphor, and
text-only scenes look fine. To add a new icon, write an `ic_<name>(d, cx, cy, s, a, bg)` function in
`scripts/render.py` (draw with `mix(color, a, bg)` so it fades) and register it in `ICONS`.

## Text length guidance

Titles and headings auto-shrink to fit one line, but keep them under ~45 characters. Card bodies
fit about 8–12 words; list items one line (~50 characters); numbered-item bodies ~15 words. The
screen should carry the idea in a few words while the narration carries the full sentence — if a
line reads like a paragraph, cut it.

See `example-slide-rule.json` for a complete nine-scene example of every type.
