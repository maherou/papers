#!/usr/bin/env python3
"""Extract plain text from a paper PDF, one block per page.

Optional helper for the article-quiz skill. Output marks each page with a
line of the form "=== Page N ===" so quotes can be located by page.

Backends, tried in order: pdftotext (poppler), pypdf, PyMuPDF (fitz).

Usage:
    python3 scripts/extract_text.py paper.pdf            # print to stdout
    python3 scripts/extract_text.py paper.pdf -o paper.txt
"""

import argparse
import shutil
import subprocess
import sys

PAGE_MARK = "=== Page {} ==="


def _pdftotext(path):
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    out = subprocess.run([exe, "-enc", "UTF-8", path, "-"],
                         check=True, capture_output=True).stdout
    # pdftotext separates pages with a form feed.
    pages = out.decode("utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def _pypdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    return [page.extract_text() or "" for page in PdfReader(path).pages]


def _fitz(path):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None
    with fitz.open(path) as doc:
        return [page.get_text() for page in doc]


def extract_pages(path):
    """Return a list of page strings, or raise RuntimeError if no backend works."""
    for backend in (_pdftotext, _pypdf, _fitz):
        pages = backend(path)
        if pages is not None:
            return pages
    raise RuntimeError(
        "No PDF text backend found. Install poppler (pdftotext), "
        "or `pip install pypdf`, or `pip install pymupdf`.")


def extract_text(path):
    pages = extract_pages(path)
    return "\n".join(f"{PAGE_MARK.format(i)}\n{text.rstrip()}\n"
                     for i, text in enumerate(pages, start=1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output", help="write to this file instead of stdout")
    args = ap.parse_args(argv)
    try:
        text = extract_text(args.pdf)
    except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
