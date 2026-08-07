"""Generate the meta-analysis forest plot used in the systematic-reviews chapter.

A fictional random-effects meta-analysis of nine studies of discharge NT-proBNP
(>= 1,000 vs < 1,000 pg/mL) and 30-day readmission after acute heart failure.
The book's own simulated cohort (Chapter: article structure) appears as one row
so the worked example threads through both a primary study and its synthesis.

The study estimates are hardcoded constants (no RNG), so the figure is
reproducible byte-for-byte regardless of numpy/pandas version. Pooling uses the
DerSimonian-Laird random-effects estimator; heterogeneity is summarised with I^2
and tau^2, and a 95% prediction interval is drawn under the pooled diamond.

Output: figures/sw/forest-meta.png

Run
---
    python figures/meta_forest.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator

BASE = Path(__file__).resolve().parent
OUT = BASE / "sw" / "forest-meta.png"

# ── register the institutional font if the bundled TTFs are present ──────────────
_FONT_DIR = BASE.parent / "fonts" / "glauca"
if _FONT_DIR.is_dir():
    for _ttf in _FONT_DIR.glob("IBMPlex*.ttf"):
        try:
            fm.fontManager.addfont(str(_ttf))
        except Exception:
            pass

GLAUCA_RC = {
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "axes.edgecolor": "#dde6ea",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.grid": False,
    "xtick.color": "#55646d",
    "ytick.color": "#55646d",
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 9,
    "axes.labelcolor": "#16222a",
    "axes.labelsize": 9.5,
    "text.color": "#16222a",
    "font.family": "sans-serif",
    "font.sans-serif": ["IBM Plex Sans", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.facecolor": "#ffffff",
    "savefig.pad_inches": 0.15,
}

INK = "#16222a"
ACCENT = "#0b62cf"   # Glauca blue mark
MUTED = "#55646d"

# ── fictional study estimates: (label, year, odds ratio, 95% CI low, high) ──────
# Ordered oldest to newest; the final row is the book's own simulated cohort.
STUDIES = [
    ("Alvarez et al.",      2016, 1.55, 1.20, 2.00),
    ("Bianchi et al.",      2017, 1.05, 0.88, 1.25),
    ("Costa et al.",        2018, 1.48, 1.18, 1.86),
    ("Duarte et al.",       2019, 1.02, 0.74, 1.40),
    ("Ferreira et al.",     2020, 1.70, 1.34, 2.16),
    ("Gomes et al.",        2021, 1.22, 1.00, 1.49),
    ("Hansen et al.",       2022, 1.12, 0.90, 1.39),
    ("Ito et al.",          2023, 1.40, 1.12, 1.75),
    # Fitted on figures/sw/cohort.csv: adjusted OR for NT-proBNP >= 1,000 vs
    # < 1,000 pg/mL, the same dichotomised contrast the other eight rows report.
    ("This cohort (Jacinto)", 2026, 1.47, 1.24, 1.75),
]


def dersimonian_laird(logor, se):
    """Return (pooled_logor, pooled_se, tau2, i2, Q) for a random-effects pool."""
    k = len(logor)
    w = [1.0 / s**2 for s in se]
    fixed_mean = sum(wi * yi for wi, yi in zip(w, logor)) / sum(w)
    Q = sum(wi * (yi - fixed_mean) ** 2 for wi, yi in zip(w, logor))
    c = sum(w) - sum(wi**2 for wi in w) / sum(w)
    tau2 = max(0.0, (Q - (k - 1)) / c) if c > 0 else 0.0
    wre = [1.0 / (s**2 + tau2) for s in se]
    pooled = sum(wi * yi for wi, yi in zip(wre, logor)) / sum(wre)
    pooled_se = math.sqrt(1.0 / sum(wre))
    i2 = max(0.0, (Q - (k - 1)) / Q) * 100 if Q > 0 else 0.0
    return pooled, pooled_se, tau2, i2, Q, wre


def main() -> None:
    labels = [f"{n}, {y}" for n, y, *_ in STUDIES]
    orr = [s[2] for s in STUDIES]
    lo = [s[3] for s in STUDIES]
    hi = [s[4] for s in STUDIES]
    logor = [math.log(o) for o in orr]
    se = [(math.log(h) - math.log(l)) / (2 * 1.959964) for l, h in zip(lo, hi)]

    pooled, pooled_se, tau2, i2, Q, wre = dersimonian_laird(logor, se)
    pooled_or = math.exp(pooled)
    p_lo = math.exp(pooled - 1.959964 * pooled_se)
    p_hi = math.exp(pooled + 1.959964 * pooled_se)
    # 95% prediction interval (t on k-2 df); k = 9 -> t ~ 2.365
    k = len(STUDIES)
    t = 2.365
    pi_half = t * math.sqrt(tau2 + pooled_se**2)
    pi_lo, pi_hi = math.exp(pooled - pi_half), math.exp(pooled + pi_half)

    wsum = sum(wre)
    weights = [100 * w / wsum for w in wre]
    mmax = max(wre)
    msize = [6 + 9 * (w / mmax) for w in wre]  # marker side scaled by weight

    plt.rcParams.update(GLAUCA_RC)
    fig, ax = plt.subplots(figsize=(8.2, 4.9))

    n = len(STUDIES)
    ys = list(range(n, 0, -1))  # top study highest on the axis
    yd = 0                      # pooled row

    ax.axvline(1.0, color=MUTED, lw=0.9, ls=(0, (4, 3)), zorder=1)

    for y, o, l, h, ms in zip(ys, orr, lo, hi, msize):
        ax.plot([l, h], [y, y], color=INK, lw=1.3, zorder=2)
        ax.plot(o, y, "s", color=ACCENT, ms=ms, zorder=3)

    dh = 0.30
    diamond = Polygon(
        [(p_lo, yd), (pooled_or, yd + dh), (p_hi, yd), (pooled_or, yd - dh)],
        closed=True, facecolor=INK, edgecolor=INK, zorder=4,
    )
    ax.add_patch(diamond)
    ax.plot([pi_lo, pi_hi], [yd, yd], color=INK, lw=1.0, ls=(0, (2, 2)), zorder=3)

    ax.set_yticks(ys + [yd])
    ax.set_yticklabels(labels + ["Random-effects pooled"], fontsize=9)
    ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.tick_params(axis="y", length=0)

    ax.set_xscale("log")
    ax.set_xlim(0.7, 2.6)
    ax.set_ylim(-1.5, n + 1.7)
    ax.xaxis.set_major_locator(FixedLocator([0.7, 1.0, 1.5, 2.0, 2.5]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FixedFormatter(["0.7", "1.0", "1.5", "2.0", "2.5"]))
    ax.set_xlabel("Odds ratio for 30-day readmission (log scale)")

    # right-hand columns: x in axes fraction (>1 = right of the plot), y in data
    trans = ax.get_yaxis_transform()
    x_or, x_wt = 1.04, 1.55
    ax.text(x_or, n + 1.25, "OR (95% CI)", fontsize=8.2, fontweight="bold",
            va="center", ha="left", color=INK, transform=trans)
    ax.text(x_wt, n + 1.25, "Weight", fontsize=8.2, fontweight="bold",
            va="center", ha="left", color=INK, transform=trans)
    for y, o, l, h, w in zip(ys, orr, lo, hi, weights):
        ax.text(x_or, y, f"{o:.2f} ({l:.2f}–{h:.2f})", fontsize=8.2,
                va="center", ha="left", color=INK, transform=trans)
        ax.text(x_wt, y, f"{w:.1f}%", fontsize=8.2, va="center", ha="left",
                color=MUTED, transform=trans)
    ax.text(x_or, yd, f"{pooled_or:.2f} ({p_lo:.2f}–{p_hi:.2f})", fontsize=8.2,
            fontweight="bold", va="center", ha="left", color=INK, transform=trans)

    # favours labels inside the plot, above the study rows
    ax.text(0.85, n + 1.25, "favours lower\nNT-proBNP", fontsize=7.2, color=MUTED,
            ha="center", va="center", linespacing=1.1)
    ax.text(1.9, n + 1.25, "favours higher\nNT-proBNP", fontsize=7.2, color=MUTED,
            ha="center", va="center", linespacing=1.1)

    # heterogeneity annotation below the axis
    # -0.17, not -0.20: at -0.20 the line falls below the figure canvas and the
    # renderer clips it (bottom=0.17 leaves only 0.02 of figure height there).
    ax.text(0.0, -0.17,
            "Random effects (DerSimonian-Laird).  "
            rf"$I^2$ = {i2:.0f}%,  $\tau^2$ = {tau2:.3f}.  "
            f"95% prediction interval {pi_lo:.2f}–{pi_hi:.2f} (dotted).",
            fontsize=7.6, va="top", ha="left", color=MUTED, transform=ax.transAxes)

    fig.subplots_adjust(left=0.22, right=0.64, top=0.92, bottom=0.17)
    fig.savefig(OUT)
    print(f"wrote {OUT}  (pooled OR={pooled_or:.3f}, I2={i2:.0f}%, tau2={tau2:.3f})")


if __name__ == "__main__":
    main()
