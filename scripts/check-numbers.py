#!/usr/bin/env python3
"""Cohort-consistency check for The Working Draft.

The book's didactic conceit is that every quoted descriptive comes from one of
the two committed cohorts. Nothing enforced that, and the numbers drifted: a
baseline table that disagreed with its own dataset, arm sizes quoted three
different ways, a missingness figure attached to a variable that had none.

This recomputes the load-bearing descriptives straight from the CSVs and fails
if a chapter still quotes a superseded value. It does not check the regression
estimates (those need statsmodels; `figures/predmodel.py` and
`figures/meta_forest.py` print theirs on every run) — only the counts, rates,
and group sizes, which are the ones that drift silently.

Pure standard library. Run from the repo root:

    python scripts/check-numbers.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SW = ROOT / "figures" / "sw" / "cohort.csv"
DV = ROOT / "figures" / "dataviz" / "cohort.csv"
SOURCES = sorted((ROOT / "chapters").glob("*.qmd")) + [ROOT / "index.qmd"]
ARMS = ["Placebo", "ACEi", "ARB", "CCB"]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def truthy(v: str) -> bool:
    return v.strip().lower() in {"true", "1", "yes"}


def main() -> int:
    if not (SW.exists() and DV.exists()):
        print("check-numbers: cohort CSVs missing", file=sys.stderr)
        return 1

    sw, dv = rows(SW), rows(DV)
    readmitted = sum(1 for r in sw if truthy(r["readmit_30d"]))
    nt_present = sum(1 for r in sw if r["ntprobnp_discharge"].strip())
    counts = {a: sum(1 for r in dv if r["treatment"] == a) for a in ARMS}

    # Each entry: a value the prose must agree with, and how the book writes it.
    expected = {
        "heart-failure cohort size": f"{len(sw):,}",
        "readmitted group": f"{readmitted:,}",
        "not-readmitted group": f"{len(sw) - readmitted:,}",
        "NT-proBNP complete cases": f"{nt_present:,}",
        "NT-proBNP missing": f"{len(sw) - nt_present}",
        "hypertension cohort size": f"{len(dv):,}",
    }
    text = {p: p.read_text(encoding="utf-8") for p in SOURCES if p.exists()}
    joined = "\n".join(text.values())

    problems: list[str] = []
    for label, value in expected.items():
        if value not in joined:
            problems.append(f"no chapter quotes the {label} ({value})")

    # Every `n = a/b/c/d` run of four must be the realised arm sizes. This is the
    # shape that was wrong in three chapters at once.
    arm_sizes = "/".join(str(counts[a]) for a in ARMS)
    quad = re.compile(r"n = (\d{2,4}/\d{2,4}/\d{2,4}/\d{2,4})")
    for path, body in text.items():
        for m in quad.finditer(body):
            if m.group(1) != arm_sizes:
                line = body.count("\n", 0, m.start()) + 1
                problems.append(
                    f"{path.relative_to(ROOT)}:{line}: arm sizes {m.group(1)} "
                    f"do not match the cohort ({arm_sizes})"
                )
    # Same check for the spelled-out form used in the CONSORT example.
    named = re.compile(r"Placebo n = (\d+), ACEi n = (\d+), ARB n = (\d+), CCB n = (\d+)")
    for path, body in text.items():
        for m in named.finditer(body):
            if list(map(int, m.groups())) != [counts[a] for a in ARMS]:
                line = body.count("\n", 0, m.start()) + 1
                problems.append(
                    f"{path.relative_to(ROOT)}:{line}: arm sizes "
                    f"{'/'.join(m.groups())} do not match the cohort ({arm_sizes})"
                )

    # The readmission rate is quoted in nine places; they must agree with the data.
    rate = f"{100 * readmitted / len(sw):.1f}%"
    for path, body in text.items():
        for m in re.finditer(r"readmission rate was (\d+\.\d+%)", body):
            if m.group(1) != rate:
                line = body.count("\n", 0, m.start()) + 1
                problems.append(
                    f"{path.relative_to(ROOT)}:{line}: readmission rate "
                    f"{m.group(1)} does not match the cohort ({rate})"
                )

    if problems:
        print("check-numbers FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(
        f"check-numbers OK: heart failure n={len(sw):,} "
        f"({readmitted:,} readmitted, {rate}); hypertension n={len(dv):,} "
        f"(arms {arm_sizes}); all quoted descriptives agree with the CSVs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
