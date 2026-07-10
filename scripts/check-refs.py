#!/usr/bin/env python3
"""Pre-render integrity check for The Working Draft.

Fails (exit 1) if any chapter cites a bibliography key that is not defined, or
references a figure/asset path that does not exist on disk. Quarto's own
`quarto render` exits 0 on both of these, so this guard runs first in CI to
keep undefined citations and broken image paths from reaching the built site.

Pure standard library. Run from the repo root:

    python scripts/check-refs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Chapters + top-level content files that carry prose, citations, and figures.
QMD_FILES = sorted((ROOT / "chapters").glob("*.qmd")) + [
    ROOT / "index.qmd",
    ROOT / "references.qmd",
]
BIB_FILES = sorted((ROOT / "assets").glob("*.bib"))
CONFIG = ROOT / "_quarto.yml"

# A Pandoc citation key: @ + letter, then word chars, then a 4-digit year, then
# an optional lowercase disambiguator (e.g. @page2021prisma, @smith2019a).
# The mandatory 4-digit run means Quarto cross-references (@fig-x, @sec-y,
# @tbl-z) never match, so they are not mistaken for citations.
CITE_RE = re.compile(r"(?<![\w@])@([A-Za-z][\w:-]*?[0-9]{4}[a-z]*)\b")
BIBKEY_RE = re.compile(r"^@\w+\{\s*([^,\s]+)\s*,", re.MULTILINE)
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
# figures/... or assets/... paths referenced anywhere in _quarto.yml.
CONFIG_ASSET_RE = re.compile(r"((?:figures|assets)/[\w./-]+\.(?:png|jpe?g|svg|pdf))")


def strip_code(text: str) -> str:
    """Drop fenced code blocks so code contents cannot masquerade as citations."""
    return FENCE_RE.sub("", text)


def bib_keys() -> set[str]:
    keys: set[str] = set()
    for bib in BIB_FILES:
        keys |= set(BIBKEY_RE.findall(bib.read_text(encoding="utf-8")))
    return keys


def main() -> int:
    problems: list[str] = []

    defined = bib_keys()
    if not defined:
        problems.append(f"no bibliography keys found in {[b.name for b in BIB_FILES]}")

    # 1. Undefined citations.
    for qmd in QMD_FILES:
        if not qmd.exists():
            continue
        prose = strip_code(qmd.read_text(encoding="utf-8"))
        for key in sorted(set(CITE_RE.findall(prose))):
            if key not in defined:
                problems.append(f"{qmd.relative_to(ROOT)}: undefined citation @{key}")

    # 2. Missing figure/image paths referenced from chapters.
    for qmd in QMD_FILES:
        if not qmd.exists():
            continue
        for raw in IMG_RE.findall(qmd.read_text(encoding="utf-8")):
            if raw.startswith(("http://", "https://", "data:")):
                continue
            target = (qmd.parent / raw).resolve()
            if not target.exists():
                problems.append(f"{qmd.relative_to(ROOT)}: missing image {raw}")

    # 3. Missing asset paths referenced from _quarto.yml (cover, OG, favicon).
    if CONFIG.exists():
        for raw in CONFIG_ASSET_RE.findall(CONFIG.read_text(encoding="utf-8")):
            if not (ROOT / raw).exists():
                problems.append(f"_quarto.yml: missing asset {raw}")

    if problems:
        print("check-refs FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(
        f"check-refs OK: {len(defined)} bib keys, "
        f"{len([q for q in QMD_FILES if q.exists()])} source files, no broken references."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
