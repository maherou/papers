---
name: article-quiz
description: Turn a paper PDF into a "Take the Challenge" multiple-choice quiz. Reads the PDF, finds the paper's key themes, and writes a versioned quiz.json (schema version 1) for the quiz player in this papers repo, plus a quiz-summary.md for review. Every question is grounded in a verbatim quote from the paper. Use whenever Mike asks for a quiz, a "Take the Challenge" quiz, quiz questions, or a quiz.json for a paper, even if he does not say "skill".
---

# Article Quiz

Skill version: **0.1**. Write `"generated_by": "article-quiz skill v0.1"` in every file.

You turn one paper PDF into a 5 to 10 question multiple-choice quiz. The output is a data file for an existing web player; never write HTML or a player yourself.

## Inputs

- **Required:** the paper PDF (the same file readers see on the website).
- **Optional:** title, authors, Zenodo DOI, PDF URL, pitch-video URL. Papers usually print the title, authors and DOI on page 1; take them from there when the user does not give them. Do not guess URLs. If the DOI is known but the PDF URL is not, ask for it, or leave `pdf_url` as `""` and say so. Leave `video_url` as `""` unless the user supplies it.

## Workflow

### 1. Extract the text

If `scripts/extract_text.py` is available, run `python3 scripts/extract_text.py paper.pdf -o paper.txt`. Otherwise extract the text any way you can (pypdf, pdftotext, or reading the PDF directly). Keep track of page numbers and section headings so you can fill in `location`.

### 2. Find the themes

Read the whole paper. List its key themes or claims: the main contributions, arguments, recommendations, findings and definitions a careful reader should come away with. Skip incidental detail (biographical notes, acknowledgments, licensing, AI-use statements, reference lists, minor footnote trivia).

- One question per theme. The number of distinct themes sets the question count.
- **Minimum 5, maximum 10.** Do not pad to reach 10. For a short paper, split a broad theme into distinct claims to reach 5; for a long paper, keep the 10 most central.

### 3. Write the questions

For each theme, write one question:

- **Grounding:** the question and its correct answer must follow directly from a passage you can quote verbatim. No question may rest on inference beyond the text, outside knowledge, or the paper's references.
- **`quote`:** copy the passage exactly as it appears in the paper, one or two sentences, enough to show the answer. Keep the paper's own wording, punctuation and spelling. Do not join text across a page break, footnote or heading, do not include footnote markers, and do not paraphrase or use ellipses. A sentence fragment is fine if it is contiguous.
- **`location`:** section name and page, for example `"When Activities Become Slide Rules (p. 2)"`, `"Abstract (p. 1)"`, `"Footnote 2 (p. 2)"`. Use `""` only if neither can be determined.
- **`type`:**
  - `single`: exactly one correct choice. Use for most questions.
  - `multi` (select all that apply): two or more correct choices and at least one incorrect choice. Use for a minority of questions, only where the paper itself lists several items. Say "Select all that apply." in the prompt.
- **Choices:** about four (3 to 5 allowed), ids `a`, `b`, `c`, ... in order.
  - For `single`: one correct answer, one plausible **near-miss**, and two **clearly wrong** distractors. Take near-misses from the paper's own ideas (a neighboring claim, the opposite case the paper discusses, a term the paper uses for something else), not invented material.
  - Make choices similar in length and style so the correct one does not stand out.
  - Vary the position of the correct answer across questions.
  - Avoid "all of the above", "none of the above", and negatively worded prompts ("Which is NOT...").
- **`prompt`:** one clear question a reader of the paper can answer without the paper open.
- **`explanation`:** one to three sentences on what the question was probing and why the correct answer is correct. When useful, say why the near-miss is wrong.
- **`theme`:** a short label (3 to 8 words) for the theme.
- **`id`:** `q1`, `q2`, ... in order.

### 4. Verify before emitting

For every question, confirm the `quote` appears in the extracted text. Compare after collapsing whitespace and line breaks and treating curly and straight quotes, and hyphens and dashes, as equal. If a quote is not found, fix it by copying it again from the text; never keep an unverified quote. Then check the rules: 5 to 10 questions, unique ids, choice counts, exactly one correct for `single`, two or more correct plus one incorrect for `multi`, no empty fields.

If `scripts/validate_quiz.py` is available, run:

```
python3 scripts/validate_quiz.py quiz.json --pdf paper.pdf
```

and fix every ERROR before handing over the files. It must print `OK`.

### 5. Write the outputs

Write two files:

1. **`quiz.json`** in exactly the schema below.
2. **`quiz-summary.md`** for Mike's review, in this shape:

   ```markdown
   # Quiz summary: <title>

   Generated <YYYY-MM-DD> by article-quiz skill v0.1 · <N> questions (<S> single, <M> multi) · all quotes verified

   ## Themes
   1. <theme of q1>
   ...

   ## Questions
   ### q1 · single · <theme>
   <prompt>
   - a. <text>
   - **b. <text>** ✓
   ...
   > <quote> (<location>)
   ```

Then tell Mike, in a few lines: the question count, the themes, anything you could not determine (for example a missing PDF or video URL), and the suggested publish path `quizzes/<slug>/quiz.json` in this papers repository.

## Schema (schema version 1)

```json
{
  "schema_version": 1,
  "generated_by": "article-quiz skill v0.1",
  "generated_on": "YYYY-MM-DD",
  "paper": {
    "title": "Full title, including any subtitle",
    "authors": ["Author One", "Author Two"],
    "doi": "10.5281/zenodo.XXXXXXX",
    "pdf_url": "https://...",
    "video_url": "https://..."
  },
  "questions": [
    {
      "id": "q1",
      "type": "single",
      "theme": "Short theme label",
      "prompt": "Question text?",
      "choices": [
        {"id": "a", "text": "Choice text", "correct": false},
        {"id": "b", "text": "Choice text", "correct": true},
        {"id": "c", "text": "Choice text", "correct": false},
        {"id": "d", "text": "Choice text", "correct": false}
      ],
      "explanation": "One to three sentences.",
      "quote": "Verbatim passage from the paper.",
      "location": "Section name (p. N)"
    }
  ]
}
```

Rules:

- `doi` is the bare DOI (`10.5281/zenodo.123`), not a URL. `pdf_url` and `video_url` are `https://` URLs or `""`.
- Use these fields only; add no others. Every field shown is required.
- `generated_on` is today's date.
- Write UTF-8 JSON with real characters (curly quotes, em dashes) as they appear in the paper, not escapes.

`schema/quiz-v1.schema.json` in the repository holds the formal JSON Schema, and `examples/sample-quiz.json` is a complete worked example.
