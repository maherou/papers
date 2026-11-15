#!/usr/bin/env python3
"""Validate an article-quiz question file before publishing.

Checks the structure against schema version 1 (see schema/quiz-v1.schema.json)
plus the rules a JSON Schema cannot express. With --pdf or --text, also checks
that every quote appears verbatim in the paper (after normalizing whitespace,
curly quotes and dashes, which PDF extraction mangles).

Standard library only. Exit status: 0 valid, 1 invalid, 2 usage or I/O error.

Usage:
    python3 scripts/validate_quiz.py quiz.json
    python3 scripts/validate_quiz.py quiz.json --pdf paper.pdf
    python3 scripts/validate_quiz.py quiz.json --text paper.txt
"""

import argparse
import json
import os
import re
import sys
import unicodedata

SUPPORTED_SCHEMA_VERSIONS = (1,)
MIN_QUESTIONS, MAX_QUESTIONS = 5, 10
MIN_CHOICES, MAX_CHOICES = 3, 5
DOI_RE = re.compile(r"^10\.\S+/\S+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_CHAR_MAP = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-", "­": None, "​": None,
})


def normalize(text):
    """Normalize text so a quote matches PDF-extracted text despite layout noise."""
    text = unicodedata.normalize("NFKC", text).translate(_CHAR_MAP)
    text = re.sub(r"^=== Page \d+ ===$", " ", text, flags=re.M)
    text = re.sub(r"\s+", " ", text)
    # Dashes are often set off by spaces in one source and not the other.
    text = re.sub(r" ?- ?", "-", text)
    return text.strip()


def load_paper_text(pdf=None, text=None):
    if text:
        with open(text, encoding="utf-8") as fh:
            return fh.read()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from extract_text import extract_text
    return extract_text(pdf)


def _nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def validate(quiz, paper_text=None):
    """Return (errors, warnings) as lists of strings."""
    errors, warnings = [], []
    err, warn = errors.append, warnings.append

    if not isinstance(quiz, dict):
        return ["top level must be a JSON object"], warnings

    version = quiz.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        err(f"unsupported schema_version {version!r}; this validator supports "
            f"{', '.join(map(str, SUPPORTED_SCHEMA_VERSIONS))}")
        return errors, warnings

    allowed_top = {"schema_version", "generated_by", "generated_on", "paper", "questions"}
    for key in sorted(set(quiz) - allowed_top):
        err(f"unknown top-level field {key!r}")
    if not _nonempty_str(quiz.get("generated_by")):
        err("generated_by is missing or empty")
    if not (isinstance(quiz.get("generated_on"), str) and DATE_RE.match(quiz["generated_on"])):
        err("generated_on must be a YYYY-MM-DD date")

    paper = quiz.get("paper")
    if not isinstance(paper, dict):
        err("paper is missing or not an object")
    else:
        if not _nonempty_str(paper.get("title")):
            err("paper.title is missing or empty")
        authors = paper.get("authors")
        if not (isinstance(authors, list) and authors and all(_nonempty_str(a) for a in authors)):
            err("paper.authors must be a non-empty list of names")
        for key in ("doi", "pdf_url", "video_url"):
            if key not in paper:
                err(f"paper.{key} is missing (use \"\" if unknown)")
            elif not isinstance(paper[key], str):
                err(f"paper.{key} must be a string")
        if isinstance(paper.get("doi"), str):
            if not paper["doi"]:
                warn("paper.doi is empty")
            elif paper["doi"].startswith("http"):
                err("paper.doi must be the bare DOI (10.xxxx/...), not a URL")
            elif not DOI_RE.match(paper["doi"]):
                err(f"paper.doi {paper['doi']!r} does not look like a DOI")
        for key in ("pdf_url", "video_url"):
            value = paper.get(key)
            if isinstance(value, str):
                if not value:
                    warn(f"paper.{key} is empty")
                elif not value.startswith("https://"):
                    err(f"paper.{key} must be an https:// URL")
        for key in sorted(set(paper) - {"title", "authors", "doi", "pdf_url", "video_url"}):
            err(f"unknown field paper.{key}")

    questions = quiz.get("questions")
    if not isinstance(questions, list):
        err("questions is missing or not a list")
        return errors, warnings
    if not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
        err(f"quiz has {len(questions)} questions; must have {MIN_QUESTIONS} to {MAX_QUESTIONS}")

    norm_paper = normalize(paper_text) if paper_text is not None else None
    seen_ids, correct_positions = set(), []
    allowed_q = {"id", "type", "theme", "prompt", "choices", "explanation", "quote", "location"}

    for index, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            err(f"question {index} is not an object")
            continue
        label = q.get("id") if _nonempty_str(q.get("id")) else f"question {index}"
        if not (isinstance(q.get("id"), str) and re.match(r"^q[0-9]+$", q["id"])):
            err(f"{label}: id must look like q1, q2, ...")
        elif q["id"] in seen_ids:
            err(f"{label}: duplicate question id")
        else:
            seen_ids.add(q["id"])
        for key in sorted(set(q) - allowed_q):
            err(f"{label}: unknown field {key!r}")

        qtype = q.get("type")
        if qtype not in ("single", "multi"):
            err(f"{label}: type must be 'single' or 'multi', got {qtype!r}")
        for key in ("theme", "prompt", "explanation", "quote"):
            if not _nonempty_str(q.get(key)):
                err(f"{label}: {key} is missing or empty")
        if "location" not in q:
            err(f"{label}: location is missing (use \"\" if unknown)")
        elif not isinstance(q["location"], str):
            err(f"{label}: location must be a string")
        elif not q["location"].strip():
            warn(f"{label}: location is empty")

        choices = q.get("choices")
        if not isinstance(choices, list):
            err(f"{label}: choices is missing or not a list")
            continue
        if not MIN_CHOICES <= len(choices) <= MAX_CHOICES:
            err(f"{label}: has {len(choices)} choices; must have {MIN_CHOICES} to {MAX_CHOICES}")
        choice_ids, n_correct = set(), 0
        for c_index, c in enumerate(choices, start=1):
            if not isinstance(c, dict):
                err(f"{label}: choice {c_index} is not an object")
                continue
            cid = c.get("id")
            if not (isinstance(cid, str) and re.match(r"^[a-z]$", cid)):
                err(f"{label}: choice {c_index} id must be one lowercase letter")
            elif cid in choice_ids:
                err(f"{label}: duplicate choice id {cid!r}")
            else:
                choice_ids.add(cid)
            if not _nonempty_str(c.get("text")):
                err(f"{label}: choice {cid or c_index} text is missing or empty")
            if not isinstance(c.get("correct"), bool):
                err(f"{label}: choice {cid or c_index} correct must be true or false")
            elif c["correct"]:
                n_correct += 1
                if qtype == "single":
                    correct_positions.append(c_index)
            for key in sorted(set(c) - {"id", "text", "correct"}):
                err(f"{label}: choice {cid or c_index} has unknown field {key!r}")
        if qtype == "single" and n_correct != 1:
            err(f"{label}: single question must have exactly 1 correct choice, has {n_correct}")
        if qtype == "multi":
            if n_correct < 2:
                err(f"{label}: multi question must have at least 2 correct choices, has {n_correct}")
            if n_correct == len(choices):
                err(f"{label}: multi question needs at least one incorrect choice")

        if norm_paper is not None and _nonempty_str(q.get("quote")):
            if normalize(q["quote"]) not in norm_paper:
                err(f"{label}: quote not found verbatim in the paper text: "
                    f"{q['quote'][:80]!r}{'...' if len(q['quote']) > 80 else ''}")

    if isinstance(questions, list) and questions:
        n_multi = sum(1 for q in questions if isinstance(q, dict) and q.get("type") == "multi")
        if n_multi * 2 > len(questions):
            warn(f"{n_multi} of {len(questions)} questions are multi; the spec calls for a minority")
        if len(correct_positions) >= 4 and len(set(correct_positions)) == 1:
            warn(f"every single question has its correct answer in position {correct_positions[0]}")
    if paper_text is None:
        warn("quotes not checked against the paper (pass --pdf or --text)")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate an article-quiz question file.")
    ap.add_argument("quiz", help="path to quiz.json")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--pdf", help="paper PDF to check quotes against")
    src.add_argument("--text", help="extracted paper text to check quotes against")
    args = ap.parse_args(argv)

    try:
        with open(args.quiz, encoding="utf-8") as fh:
            quiz = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {args.quiz}: {exc}", file=sys.stderr)
        return 2
    paper_text = None
    if args.pdf or args.text:
        try:
            paper_text = load_paper_text(pdf=args.pdf, text=args.text)
        except Exception as exc:  # backend or I/O failure
            print(f"error: cannot read paper text: {exc}", file=sys.stderr)
            return 2

    errors, warnings = validate(quiz, paper_text)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    n = len(quiz.get("questions", [])) if isinstance(quiz, dict) and isinstance(quiz.get("questions"), list) else 0
    if errors:
        print(f"INVALID: {args.quiz} ({len(errors)} error(s))")
        return 1
    print(f"OK: {args.quiz} ({n} questions{', quotes verified' if paper_text is not None else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
