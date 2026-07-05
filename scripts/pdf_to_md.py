#!/usr/bin/env python3
"""Convert a manuscript PDF to Markdown with page markers for medreview.

Usage: python scripts/pdf_to_md.py papers/manuscript.pdf
Writes papers/manuscript.md with <!-- page N --> markers so reviewers can
cite locations. Requires: pip install pymupdf
"""
import sys
from pathlib import Path

import fitz  # pymupdf


def main() -> None:
    pdf_path = Path(sys.argv[1])
    out_path = pdf_path.with_suffix(".md")
    doc = fitz.open(pdf_path)
    parts = []
    for i, page in enumerate(doc, start=1):
        parts.append(f"\n<!-- page {i} -->\n")
        parts.append(page.get_text("text"))
    out_path.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {out_path} ({len(doc)} pages)")


if __name__ == "__main__":
    main()
