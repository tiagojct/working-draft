#!/usr/bin/env python3
"""Pre-render integrity check for The Working Draft.

`quarto render` exits 0 on every failure mode below, so this guard runs first
in CI. Errors (exit 1):

  1. a citation key that no .bib file defines
  2. a bibliography key defined twice (silently deduped in HTML, hard-fails
     the Typst PDF build)
  3. a cross-reference (@fig-, @tbl-, @sec-, @eq-) with no matching label
  4. an image or _quarto.yml asset path that is not on disk
  5. an internal .qmd link whose target file or #anchor does not exist
  6. a chapter file absent from the _quarto.yml chapters list (invisible in
     the book), or a _quarto.yml entry pointing at a missing file
  7. an image with no alt text and no fig-alt attribute

Warnings (reported, exit 0): figure files on disk that nothing references,
and cross-reference labels that nothing cites.

Pure standard library. Run from the repo root:

    python scripts/check-refs.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Chapters + top-level content files that carry prose, citations, and figures.
QMD_FILES = sorted((ROOT / "chapters").glob("*.qmd")) + [
    ROOT / "index.qmd",
    ROOT / "references.qmd",
]
BIB_FILES = sorted((ROOT / "assets").glob("*.bib"))
CONFIG = ROOT / "_quarto.yml"
FIGURE_DIRS = [ROOT / "figures" / "sw", ROOT / "figures" / "dataviz"]

# A Pandoc citation key: @ + letter, then word chars, then a 4-digit year, then
# an optional lowercase disambiguator (e.g. @page2021prisma, @smith2019a).
# The mandatory 4-digit run means Quarto cross-references (@fig-x, @sec-y,
# @tbl-z) never match, so they are not mistaken for citations.
CITE_RE = re.compile(r"(?<![\w@])@([A-Za-z][\w:-]*?[0-9]{4}[a-z]*)\b")
BIBKEY_RE = re.compile(r"^@\w+\{\s*([^,\s]+)\s*,", re.MULTILINE)
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)(\{[^}]*\})?")
FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
# figures/... or assets/... paths referenced anywhere in _quarto.yml.
CONFIG_ASSET_RE = re.compile(r"((?:figures|assets)/[\w./-]+\.(?:png|jpe?g|svg|pdf))")

XREF_KINDS = "fig|tbl|sec|eq"
# Quarto ids are alphanumerics, hyphens, and underscores. Excluding the period
# matters: it is what lets `@fig-bar.` at the end of a sentence resolve to
# `fig-bar`, exactly as Quarto's own parser reads it.
XREF_ID = r"[A-Za-z0-9_-]+"
# A label is only ever declared as `{#fig-x ...}` (div or image attribute) or
# as a `#| label: fig-x` cell option; a bare `#fig-x` in a link is a reference.
LABEL_RE = re.compile(rf"\{{#((?:{XREF_KINDS})-{XREF_ID})")
CELL_LABEL_RE = re.compile(rf"^#\|\s*label:\s*((?:{XREF_KINDS})-{XREF_ID})", re.M)
XREF_RE = re.compile(rf"(?<![\w@])@((?:{XREF_KINDS})-{XREF_ID})")
ANCHOR_XREF_RE = re.compile(rf"\]\(#((?:{XREF_KINDS})-{XREF_ID})\)")
# Internal link to another chapter, with an optional #anchor.
QMD_LINK_RE = re.compile(r"\]\((?!https?:)([^)#\s]*\.qmd)(#[A-Za-z0-9._-]+)?\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)
EXPLICIT_ID_RE = re.compile(r"\{#([A-Za-z0-9._-]+)")
# Chapter entries in _quarto.yml (`- chapters/foo.qmd`, `- index.qmd`).
CONFIG_QMD_RE = re.compile(r"^\s*-\s+([\w./-]+\.qmd)\s*$", re.M)


def strip_code(text: str) -> str:
    """Drop fenced code blocks so code contents cannot masquerade as citations."""
    return FENCE_RE.sub("", text)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def slugify(heading: str) -> str:
    """Approximate Pandoc's auto identifier for a heading."""
    # Strip inline markup and any trailing attribute block.
    heading = re.sub(r"\{[^}]*\}\s*$", "", heading)
    heading = re.sub(r"[*_`\[\]]", "", heading)
    # Pandoc keeps letters, digits, underscores, hyphens, periods; spaces become
    # hyphens; everything else is dropped.
    heading = heading.replace(" ", "-")
    heading = "".join(c for c in heading if c.isalnum() or c in "-_.")
    heading = heading.lower().lstrip("-")
    return re.sub(r"-{2,}", "-", heading)


def bib_keys(problems: list[str]) -> set[str]:
    """Collect every key, flagging any defined more than once across the files."""
    seen: dict[str, list[str]] = defaultdict(list)
    for bib in BIB_FILES:
        text = bib.read_text(encoding="utf-8")
        for m in BIBKEY_RE.finditer(text):
            seen[m.group(1)].append(f"{bib.name}:{line_of(text, m.start())}")
    for key, where in sorted(seen.items()):
        if len(where) > 1:
            problems.append(
                f"duplicate bibliography key @{key} defined at {', '.join(where)} "
                "(HTML dedupes silently; the Typst PDF build fails)"
            )
    return set(seen)


def registered_chapters(problems: list[str]) -> set[Path]:
    """Files listed under book.chapters in _quarto.yml, resolved to real paths."""
    listed: set[Path] = set()
    if not CONFIG.exists():
        return listed
    text = CONFIG.read_text(encoding="utf-8")
    for m in CONFIG_QMD_RE.finditer(text):
        target = ROOT / m.group(1)
        if not target.exists():
            problems.append(
                f"_quarto.yml:{line_of(text, m.start())}: chapter {m.group(1)} does not exist"
            )
        listed.add(target.resolve())
    for qmd in sorted((ROOT / "chapters").glob("*.qmd")):
        if qmd.resolve() not in listed:
            problems.append(
                f"{qmd.relative_to(ROOT)}: not listed in _quarto.yml "
                "(the chapter renders nowhere in the book)"
            )
    return listed


def main() -> int:
    problems: list[str] = []
    warnings: list[str] = []

    sources = [q for q in QMD_FILES if q.exists()]
    raw = {q: q.read_text(encoding="utf-8") for q in sources}
    prose = {q: strip_code(t) for q, t in raw.items()}

    defined = bib_keys(problems)
    if not defined:
        problems.append(f"no bibliography keys found in {[b.name for b in BIB_FILES]}")
    registered_chapters(problems)

    # Labels are declared in raw text (a `#| label:` lives inside a code cell);
    # references are read from prose so commented-out examples do not count.
    labels: dict[str, str] = {}
    for qmd, text in raw.items():
        for pattern in (LABEL_RE, CELL_LABEL_RE):
            for m in pattern.finditer(text):
                labels.setdefault(m.group(1), f"{qmd.relative_to(ROOT)}:{line_of(text, m.start())}")

    referenced: set[str] = set()

    for qmd in sources:
        rel = qmd.relative_to(ROOT)
        text, body = raw[qmd], prose[qmd]

        # 1. Undefined citations.
        for m in CITE_RE.finditer(body):
            if m.group(1) not in defined:
                problems.append(f"{rel}:{line_of(body, m.start())}: undefined citation @{m.group(1)}")

        # 2. Unresolved cross-references.
        for pattern in (XREF_RE, ANCHOR_XREF_RE):
            for m in pattern.finditer(body):
                name = m.group(1)
                referenced.add(name)
                if name not in labels:
                    problems.append(
                        f"{rel}:{line_of(body, m.start())}: cross-reference @{name} has no label"
                    )

        # 3. Images: path on disk, and alt text present.
        for m in IMG_RE.finditer(text):
            alt, target_raw, attrs = m.group(1), m.group(2), m.group(3) or ""
            line = line_of(text, m.start())
            if not target_raw.startswith(("http://", "https://", "data:")):
                if not (qmd.parent / target_raw).resolve().exists():
                    problems.append(f"{rel}:{line}: missing image {target_raw}")
            if not alt.strip() and "fig-alt" not in attrs:
                problems.append(
                    f"{rel}:{line}: image {target_raw} has no alt text and no fig-alt"
                )

        # 4. Internal .qmd links: target file, and #anchor if given.
        for m in QMD_LINK_RE.finditer(text):
            href, anchor = m.group(1), m.group(2)
            line = line_of(text, m.start())
            candidates = [qmd.parent / href, ROOT / href]
            target = next((c for c in candidates if c.exists()), None)
            if target is None:
                problems.append(f"{rel}:{line}: broken link to {href}")
                continue
            if anchor:
                slug = anchor[1:]
                target_text = target.read_text(encoding="utf-8")
                ids = {slugify(h) for h in HEADING_RE.findall(target_text)}
                ids |= set(EXPLICIT_ID_RE.findall(target_text))
                if slug not in ids:
                    problems.append(f"{rel}:{line}: link to {href} has no anchor #{slug}")

    # 5. Missing asset paths referenced from _quarto.yml (cover, OG, favicon).
    if CONFIG.exists():
        config_text = CONFIG.read_text(encoding="utf-8")
        for m in CONFIG_ASSET_RE.finditer(config_text):
            if not (ROOT / m.group(1)).exists():
                problems.append(
                    f"_quarto.yml:{line_of(config_text, m.start())}: missing asset {m.group(1)}"
                )

    # Warnings: nothing here breaks a build, but each one is dead weight.
    all_text = "\n".join(raw.values())
    for figures in FIGURE_DIRS:
        for asset in sorted(figures.glob("*")):
            if asset.suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg"}:
                continue
            if f"{figures.name}/{asset.name}" not in all_text:
                warnings.append(f"{asset.relative_to(ROOT)}: on disk but never referenced")
    for name, where in sorted(labels.items()):
        if name not in referenced:
            warnings.append(f"{where}: label #{name} is never cross-referenced")

    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)

    if problems:
        print("check-refs FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(
        f"check-refs OK: {len(defined)} bib keys, {len(labels)} cross-reference labels, "
        f"{len(sources)} source files, {len(warnings)} warnings, no broken references."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
