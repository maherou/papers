#!/usr/bin/env python3
"""Tests for scripts/validate_quiz.py. Run: python3 -m unittest discover tests"""

import copy
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from validate_quiz import normalize, validate  # noqa: E402

with open(os.path.join(ROOT, "examples", "sample-quiz.json"), encoding="utf-8") as fh:
    SAMPLE = json.load(fh)

# Paper text built from the sample's own quotes, with line breaks and straight
# punctuation, the way PDF extraction tends to return it.
PAPER_TEXT = "=== Page 1 ===\n" + "\n".join(
    q["quote"].replace("—", " - ").replace(", ", ",\n") for q in SAMPLE["questions"])


def sample():
    return copy.deepcopy(SAMPLE)


def errors_of(quiz, paper_text=None):
    return validate(quiz, paper_text)[0]


class AcceptsValid(unittest.TestCase):
    def test_sample_is_valid(self):
        self.assertEqual(errors_of(sample(), PAPER_TEXT), [])

    def test_normalize_matches_across_layout_noise(self):
        self.assertIn(normalize("learning—akin to’s"), normalize("learning -\nakin  to's"))


class Rejects(unittest.TestCase):
    def assertRejected(self, quiz, fragment, paper_text=None):
        errs = errors_of(quiz, paper_text)
        self.assertTrue(any(fragment in e for e in errs), f"expected {fragment!r} in {errs}")

    def test_missing_quote(self):
        quiz = sample()
        del quiz["questions"][0]["quote"]
        self.assertRejected(quiz, "q1: quote is missing")

    def test_empty_quote(self):
        quiz = sample()
        quiz["questions"][0]["quote"] = "  "
        self.assertRejected(quiz, "q1: quote is missing or empty")

    def test_quote_not_in_paper(self):
        quiz = sample()
        quiz["questions"][1]["quote"] = "Slide rules are making a comeback in classrooms."
        self.assertRejected(quiz, "q2: quote not found", PAPER_TEXT)

    def test_too_few_choices(self):
        quiz = sample()
        quiz["questions"][0]["choices"] = quiz["questions"][0]["choices"][:2]
        self.assertRejected(quiz, "q1: has 2 choices")

    def test_too_many_choices(self):
        quiz = sample()
        extra = [{"id": c, "text": "Extra", "correct": False} for c in "efg"]
        quiz["questions"][0]["choices"] += extra
        self.assertRejected(quiz, "q1: has 7 choices")

    def test_multi_with_one_correct(self):
        quiz = sample()
        for c in quiz["questions"][2]["choices"]:
            c["correct"] = c["id"] == "a"
        self.assertRejected(quiz, "q3: multi question must have at least 2 correct")

    def test_multi_all_correct(self):
        quiz = sample()
        for c in quiz["questions"][2]["choices"]:
            c["correct"] = True
        self.assertRejected(quiz, "q3: multi question needs at least one incorrect")

    def test_single_with_two_correct(self):
        quiz = sample()
        quiz["questions"][0]["choices"][0]["correct"] = True
        self.assertRejected(quiz, "q1: single question must have exactly 1 correct")

    def test_unsupported_schema_version(self):
        quiz = sample()
        quiz["schema_version"] = 2
        self.assertRejected(quiz, "unsupported schema_version 2")

    def test_missing_schema_version(self):
        quiz = sample()
        del quiz["schema_version"]
        self.assertRejected(quiz, "unsupported schema_version None")

    def test_too_few_questions(self):
        quiz = sample()
        quiz["questions"] = quiz["questions"][:4]
        self.assertRejected(quiz, "quiz has 4 questions")

    def test_too_many_questions(self):
        quiz = sample()
        for i in range(3):
            q = copy.deepcopy(quiz["questions"][0])
            q["id"] = f"q{9 + i}"
            quiz["questions"].append(q)
        self.assertRejected(quiz, "quiz has 11 questions")

    def test_duplicate_question_id(self):
        quiz = sample()
        quiz["questions"][1]["id"] = "q1"
        self.assertRejected(quiz, "duplicate question id")

    def test_bad_type(self):
        quiz = sample()
        quiz["questions"][0]["type"] = "truefalse"
        self.assertRejected(quiz, "type must be 'single' or 'multi'")

    def test_doi_as_url(self):
        quiz = sample()
        quiz["paper"]["doi"] = "https://doi.org/" + quiz["paper"]["doi"]
        self.assertRejected(quiz, "bare DOI")

    def test_non_https_link(self):
        quiz = sample()
        quiz["paper"]["video_url"] = "javascript:alert(1)"
        self.assertRejected(quiz, "paper.video_url must be an https:// URL")


if __name__ == "__main__":
    unittest.main()
