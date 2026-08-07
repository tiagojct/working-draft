"""Generate the Open Graph social card for the book's website.

Quarto's `open-graph` picks the first image on a page when no explicit one is
configured, which on the landing page is its own inline link-icon data URI. With
`site-url` set that gets concatenated into a nonsense absolute URL, so the card
has to be a real file referenced from `book: image:` in _quarto.yml.

The design is the PDF cover reduced to the 1200x630 crop every platform expects:
frost ground, blue mono eyebrow, hairline rule, IBM Plex Serif title, muted
subtitle, imprint at the foot. Keep it in sync with `wd-cover` in
assets/book-typst.typ if the cover changes.

No data, no RNG: the output is byte-stable across runs.

Output: assets/social-card.png

Run
---
    python figures/social_card.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / "assets" / "social-card.png"

# ── register the bundled IBM Plex faces so the card renders identically on CI ──
_FONT_DIR = BASE.parent / "fonts" / "glauca"
if _FONT_DIR.is_dir():
    for _ttf in _FONT_DIR.glob("IBMPlex*.ttf"):
        try:
            fm.fontManager.addfont(str(_ttf))
        except Exception:  # pragma: no cover - a missing face is not fatal
            pass

# Glauca palette, matching assets/book-typst.typ.
INK = "#16222a"
BLUE = "#0b62cf"
FROST = "#f0f4f6"
RULE = "#cdd7dc"
MUTED = "#4a5b63"

# 1200x630 at 100 dpi is the Open Graph reference size.
W_IN, H_IN, DPI = 12.0, 6.3, 100

TITLE = "The Working Draft"
SUBTITLE = "Writing and Data Visualisation for Health Researchers"
AUTHOR = "TIAGO JACINTO"
AFFILIATION = "Faculty of Medicine, University of Porto"


def main() -> None:
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=FROST)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_axis_off()
    ax.set_facecolor(FROST)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    left = 0.072
    right = 0.928

    ax.text(left, 0.845, "A FIELD GUIDE", color=BLUE, fontsize=13,
            fontfamily="IBM Plex Mono", fontweight="medium", va="center")

    ax.add_line(Line2D([left, right], [0.775, 0.775], color=RULE, linewidth=1.1))

    ax.text(left, 0.615, TITLE, color=INK, fontsize=62,
            fontfamily="IBM Plex Serif", fontweight="bold", va="center")

    ax.text(left, 0.455, SUBTITLE, color=MUTED, fontsize=23,
            fontfamily="IBM Plex Sans", va="center")

    ax.add_line(Line2D([left, left + 0.13], [0.235, 0.235], color=RULE, linewidth=1.1))

    ax.text(left, 0.155, AUTHOR, color=INK, fontsize=17,
            fontfamily="IBM Plex Sans", fontweight="bold", va="center")

    ax.text(left, 0.085, AFFILIATION, color=MUTED, fontsize=15,
            fontfamily="IBM Plex Sans", va="center")

    fig.savefig(OUT, dpi=DPI, facecolor=FROST)
    plt.close(fig)
    print(f"wrote {OUT}  ({int(W_IN * DPI)}x{int(H_IN * DPI)})")


if __name__ == "__main__":
    main()
