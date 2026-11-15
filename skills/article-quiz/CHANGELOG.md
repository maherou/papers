# Changelog

This file tracks the three versioned parts of the article-quiz skill:

- **Skill**: `SKILL.md`, recorded in each quiz as `generated_by: "article-quiz skill vX.Y"`.
- **Schema**: the question-file format, recorded in each quiz as `schema_version`. Bump it on any incompatible change.
- **Player**: `player/` at the top of this repo, which declares `PLAYER_VERSION` and `SUPPORTED_SCHEMA_VERSIONS` in `player/player.js`.

## 2026-11-14

### Player v0.1.3

- Copied into this papers repo, at `player/`. The footer link now goes back to this site's papers page (`../`).
- The skill now names this repo as the place to publish quizzes.


### Player v0.1.2

- Add an About link in the footer that opens a small panel with the copyright notice and links to the MIT and CC BY 4.0 licenses. Opening or closing it leaves quiz progress and score untouched.

## 2026-11-13

### Player v0.1.1

- Fix the footer link to the Collegeville papers page, which pointed to `papers.html` (a 404) instead of `/papers/`.

### Skill v0.1

- First version. Reads a paper PDF, finds its themes, writes 5 to 10 `single` or `multi` questions, each grounded in a verbatim quote, and emits `quiz.json` and `quiz-summary.md`.

### Schema version 1

- First version. Fields: `schema_version`, `generated_by`, `generated_on`, `paper` (`title`, `authors`, `doi`, `pdf_url`, `video_url`), and `questions` (`id`, `type`, `theme`, `prompt`, `choices`, `explanation`, `quote`, `location`).
- JSON Schema in `schema/quiz-v1.schema.json`.

### Player v0.1.0

- First version. Supports schema version 1. Intro, one-attempt questions with per-choice feedback, partial credit for `multi`, running score, end screen with share line, Copy, Web Share, and Try again.

### Tools

- `scripts/extract_text.py`: PDF text extraction with page markers (pdftotext, pypdf, or PyMuPDF).
- `scripts/validate_quiz.py`: structural checks plus quote verification against the PDF. Standard library only.
