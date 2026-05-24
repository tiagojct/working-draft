"""Generate all PNG figures for the research methods book.

Figures:
  figures/sw/     — ch.4 NT-proBNP / heart failure cohort
  figures/dataviz/ — ch.11 chart types + ch.12 pitfalls
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── inject pequod ──────────────────────────────────────────────────────────────
# The pequod package supplies the comparison palette used by the alternative
# theme in this script. It is an external sibling repo; set PEQUOD_SRC to
# override the default path, or install pequod into the active environment.
_DEFAULT_PEQUOD_SRC = Path.home() / "rokovoko" / "pequod" / "python" / "src"
PEQUOD_SRC = Path(os.environ.get("PEQUOD_SRC", _DEFAULT_PEQUOD_SRC))
if PEQUOD_SRC.is_dir() and str(PEQUOD_SRC) not in sys.path:
    sys.path.insert(0, str(PEQUOD_SRC))

try:
    import pequod  # noqa: E402
except ModuleNotFoundError as exc:
    raise SystemExit(
        f"pequod not found at {PEQUOD_SRC} and not importable from the environment.\n"
        f"Set PEQUOD_SRC=/path/to/pequod/python/src or `pip install pequod`."
    ) from exc

# ── standard imports ───────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import scipy.stats as stats
import seaborn as sns

# ── directory shortcuts ────────────────────────────────────────────────────────
BASE   = Path(__file__).parent
SW_DIR = BASE / "sw"
DV_DIR = BASE / "dataviz"

SW_DIR.mkdir(exist_ok=True)
DV_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# Theme definitions
# ══════════════════════════════════════════════════════════════════════════════

FMUP_RC = {
    "figure.facecolor":       "white",
    "axes.facecolor":         "white",
    "axes.edgecolor":         "#E0E0E0",
    "axes.linewidth":          0.8,
    "axes.spines.top":         False,
    "axes.spines.right":       False,
    "axes.grid":               True,
    "axes.grid.axis":         "y",
    "grid.color":             "#E0E0E0",
    "grid.linewidth":          0.5,
    "xtick.color":            "#5B6470",
    "ytick.color":            "#5B6470",
    "xtick.labelsize":         8.5,
    "ytick.labelsize":         8.5,
    "axes.labelcolor":        "#1A1A1A",
    "axes.labelsize":          9.5,
    "axes.titlesize":          10,
    "text.color":             "#1A1A1A",
    "legend.fontsize":         8.5,
    "legend.frameon":          False,
    "font.family":            "sans-serif",
    "font.sans-serif":        ["Atkinson Hyperlegible", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.dpi":              150,
    "savefig.dpi":             150,
    "savefig.facecolor":      "white",
    "savefig.pad_inches":      0.15,
}

PEQUOD_RC = {
    "figure.facecolor":       "#F7F3EE",
    "axes.facecolor":         "#F7F3EE",
    "axes.edgecolor":         "#BD8C68",
    "axes.linewidth":          0.8,
    "axes.spines.top":         False,
    "axes.spines.right":       False,
    "axes.grid":               True,
    "axes.grid.axis":         "y",
    "grid.color":             "#DBC9B6",
    "grid.linewidth":          0.5,
    "xtick.color":            "#835A49",
    "ytick.color":            "#835A49",
    "xtick.labelsize":         8.5,
    "ytick.labelsize":         8.5,
    "axes.labelcolor":        "#0D2F42",
    "axes.labelsize":          9.5,
    "axes.titlesize":          10,
    "text.color":             "#0D2F42",
    "legend.fontsize":         8.5,
    "legend.frameon":          False,
    "font.family":            "sans-serif",
    "font.sans-serif":        ["Atkinson Hyperlegible", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.dpi":              150,
    "savefig.dpi":             150,
    "savefig.facecolor":      "#F7F3EE",
    "savefig.pad_inches":      0.15,
}

# ══════════════════════════════════════════════════════════════════════════════
# Colour palettes
# ══════════════════════════════════════════════════════════════════════════════

FMUP4    = ["#1A1A1A", "#2B7BB9", "#D06B3A", "#3A9653"]
ARM_FMUP = dict(zip(["Placebo", "ACEi", "ARB", "CCB"], FMUP4))

FMUP_BAR   = "#FFCD00"
FMUP_DARK  = "#1A1A1A"
FMUP_MUTED = "#5B6470"

PEQUOD4 = [
    pequod.CREW_LIGHT["Starbuck"],   # #0082B1
    pequod.CREW_LIGHT["Ahab"],       # #A83732
    pequod.CREW_LIGHT["Tashtego"],   # #177C55
    pequod.CREW_LIGHT["Stubb"],      # #CA6435
]
ARM_PEQUOD     = dict(zip(["Placebo", "ACEi", "ARB", "CCB"], PEQUOD4))
PEQUOD_ACCENT  = pequod.CREW_LIGHT["Starbuck"]

# ══════════════════════════════════════════════════════════════════════════════
# Register pequod colourmaps
# ══════════════════════════════════════════════════════════════════════════════
pequod.register_cmaps()

# ══════════════════════════════════════════════════════════════════════════════
# Load cohort data
# ══════════════════════════════════════════════════════════════════════════════
cohort = pd.read_csv(DV_DIR / "cohort.csv")

# ── simulated extra data ───────────────────────────────────────────────────────
rng = np.random.default_rng(42)

# Trajectory data (30 patients per arm × 4 timepoints)
rows = []
for arm in ["Placebo", "ACEi", "ARB", "CCB"]:
    sub = cohort[cohort["treatment"] == arm].sample(
        min(30, (cohort["treatment"] == arm).sum()), random_state=42
    )
    for _, r in sub.iterrows():
        b, e = r["sbp_baseline"], r["sbp_6m"]
        for mo, val in zip(
            [0, 1, 3, 6],
            [
                b,
                b + (e - b) * 0.3  + rng.normal(0, 3),
                b + (e - b) * 0.65 + rng.normal(0, 3),
                e,
            ],
        ):
            rows.append({"id": r["id"], "treatment": arm, "month": mo, "sbp": val})
traj = pd.DataFrame(rows)
traj_summary = traj.groupby(["treatment", "month"])["sbp"].mean().reset_index()

# KM data (time to BP control per arm)
hazards = {"Placebo": 0.30, "ACEi": 0.85, "ARB": 0.65, "CCB": 0.55}
km_rows = []
for arm in ["Placebo", "ACEi", "ARB", "CCB"]:
    n = (cohort["treatment"] == arm).sum()
    t = rng.exponential(1.0 / hazards[arm], n)
    e = (t <= 6).astype(int)
    t = np.minimum(t, 6.0)
    km_rows.extend(
        {"treatment": arm, "event_time": ti, "event": ei} for ti, ei in zip(t, e)
    )
cohort_km = pd.DataFrame(km_rows)

# NT-proBNP (heart failure, 2 groups, n=200 each)
n_sw = 200
ntprobnp = pd.DataFrame(
    {
        "group": ["Readmitted"] * n_sw + ["Not readmitted"] * n_sw,
        "ntprobnp": np.concatenate(
            [
                rng.lognormal(np.log(1820), 0.8, n_sw),
                rng.lognormal(np.log(780),  0.75, n_sw),
            ]
        ),
    }
)

# ══════════════════════════════════════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════════════════════════════════════

def savefig(fig: plt.Figure, path: Path | str, rc: dict) -> None:
    fig.savefig(
        path,
        facecolor=rc["savefig.facecolor"],
        bbox_inches="tight",
        dpi=rc["savefig.dpi"],
    )
    plt.close(fig)
    print(f"  ✓ {Path(path).name}")


# ══════════════════════════════════════════════════════════════════════════════
# sw/ figures  (NT-proBNP, heart failure cohort)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── sw/ ─────────────────────────────────────────────────────────────────")

groups     = ["Readmitted", "Not readmitted"]
means      = [ntprobnp[ntprobnp["group"] == g]["ntprobnp"].mean() for g in groups]
medians    = [ntprobnp[ntprobnp["group"] == g]["ntprobnp"].median() for g in groups]
sds        = [ntprobnp[ntprobnp["group"] == g]["ntprobnp"].std() for g in groups]

# ── sw/01-ugly.png ─────────────────────────────────────────────────────────────
with plt.rc_context({"axes.facecolor": "#E8F4FF", "figure.facecolor": "#E8F4FF",
                     "axes.spines.top": True, "axes.spines.right": True,
                     "axes.spines.left": True, "axes.spines.bottom": True,
                     "axes.grid": True, "axes.grid.axis": "both",
                     "grid.color": "#AAAAAA", "font.family": "sans-serif"}):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.set_facecolor("#E8F4FF")
    colors_ugly = ["#FF0000", "#00FF00"]
    bars = ax.bar(groups, means, color=colors_ugly, edgecolor="black", linewidth=1.5)
    ax.errorbar(
        x=range(len(groups)), y=means, yerr=sds,
        fmt="none", ecolor="blue", elinewidth=2, capsize=6, capthick=2
    )
    ax.set_xlabel("group", fontsize=9)
    ax.set_ylabel("nt-probnp (pg/ml)", fontsize=9)
    ax.set_title("nt-probnp by group", fontsize=10)
    savefig(fig, SW_DIR / "01-ugly.png", {"savefig.facecolor": "#E8F4FF", "savefig.dpi": 150})

# ── sw/02-bad-bar.png ─────────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(groups, means, color=FMUP_BAR, edgecolor=FMUP_DARK, linewidth=0.7, width=0.5)
    ax.errorbar(
        x=range(len(groups)), y=means, yerr=sds,
        fmt="none", ecolor=FMUP_DARK, elinewidth=1.2, capsize=5, capthick=1.2
    )
    for bar, val in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + sds[means.index(val)] + 30,
            f"{val:,.0f}",
            ha="center", va="bottom", fontsize=8, color=FMUP_DARK
        )
    ax.set_ylabel("NT-proBNP at discharge (pg/mL)")
    ax.set_xlabel("")
    savefig(fig, SW_DIR / "02-bad-bar.png", FMUP_RC)

# ── sw/03-bad-truncated.png ───────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(groups, medians, color=FMUP_BAR, edgecolor=FMUP_DARK, linewidth=0.7, width=0.5)
    ax.set_ylim(500, None)
    for bar, val in zip(bars, medians):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 10,
            f"{val:,.0f}",
            ha="center", va="bottom", fontsize=8, color=FMUP_DARK
        )
    ax.set_ylabel("NT-proBNP at discharge (pg/mL)")
    ax.set_xlabel("")
    savefig(fig, SW_DIR / "03-bad-truncated.png", FMUP_RC)

# ── sw/04-good.png ────────────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    colors_04 = [FMUP4[2], FMUP4[1]]  # Readmitted=orange, Not readmitted=blue
    positions = [1, 2]

    for pos, grp, col in zip(positions, groups, colors_04):
        vals = ntprobnp[ntprobnp["group"] == grp]["ntprobnp"].values
        # jittered strip
        jitter = rng.uniform(-0.18, 0.18, len(vals))
        ax.scatter(pos + jitter, vals, alpha=0.2, s=12, color=col, zorder=2)
        # boxplot
        bp = ax.boxplot(
            vals,
            positions=[pos],
            widths=0.35,
            patch_artist=True,
            sym="",
            medianprops={"linewidth": 0},
            whiskerprops={"color": col, "linewidth": 1.0},
            capprops={"color": col, "linewidth": 1.0},
            boxprops={"facecolor": "none", "edgecolor": col, "linewidth": 1.0},
            flierprops={"marker": "", "markersize": 0},
        )
        # diamond median
        med = np.median(vals)
        ax.scatter(pos, med, marker="D", s=30, color=col, zorder=5)

    ax.set_yscale("log")
    ax.set_ylabel("NT-proBNP at discharge (pg/mL)")
    ax.set_xticks(positions)
    ax.set_xticklabels(groups)
    ax.text(
        0.98, 0.02,
        "n = 200 per group",
        ha="right", va="bottom",
        transform=ax.transAxes,
        fontsize=8, color=FMUP_MUTED,
    )
    savefig(fig, SW_DIR / "04-good.png", FMUP_RC)

# ── sw/05-pie-overkill.png ────────────────────────────────────────────────────
with plt.rc_context({**FMUP_RC, "axes.grid": False}):
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.pie(
        [83, 17],
        labels=["Female", "Male"],
        colors=[FMUP_DARK, "#B3BBC4"],
        autopct="%1.0f%%",
        startangle=90,
        textprops={"fontsize": 9},
        pctdistance=0.7,
    )
    ax.set_title("Sex at birth (n = 5,204)", fontsize=10)
    savefig(fig, SW_DIR / "05-pie-overkill.png", FMUP_RC)

# ── sw/06-bar-overkill.png ────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.bar(["Female", "Male"], [83, 17], color=[FMUP_DARK, "#B3BBC4"],
           edgecolor="none", width=0.5)
    ax.set_ylabel("Percentage (%)")
    ax.set_title("Sex at birth (n = 5,204)", fontsize=10)
    savefig(fig, SW_DIR / "06-bar-overkill.png", FMUP_RC)


# ══════════════════════════════════════════════════════════════════════════════
# dataviz/ pitfall figures  (ch.12)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── dataviz/ pitfalls ────────────────────────────────────────────────────")

# ── 01-pie-bad.png ────────────────────────────────────────────────────────────
with plt.rc_context({}):   # matplotlib defaults → clearly ugly contrast
    vc = cohort["bp_class_6m"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(vc.values, labels=vc.index.tolist(), autopct="%1.1f%%")
    ax.set_title("BP class at 6 months")
    savefig(fig, DV_DIR / "01-pie-bad.png", {"savefig.facecolor": "white", "savefig.dpi": 150})

# ── 01-bar-good.png ───────────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    vc   = cohort["bp_class_6m"].value_counts().sort_values()
    n_total = vc.sum()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(vc.index, vc.values, color=FMUP_DARK, height=0.5)
    for val, lbl in zip(vc.values, vc.index):
        pct = 100 * val / n_total
        ax.text(val + 3, lbl, f"{val} ({pct:.0f}%)", va="center", fontsize=8.5, color=FMUP_DARK)
    ax.set_xlabel("Participants (n)")
    ax.set_xlim(0, vc.max() * 1.25)
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    savefig(fig, DV_DIR / "01-bar-good.png", FMUP_RC)

# ── age/BMI band helpers ───────────────────────────────────────────────────────
age_bins  = [30, 45, 55, 65, 75, 85]
age_labels= ["30–44", "45–54", "55–64", "65–74", "75–85"]
bmi_bins  = [0, 22, 25, 30, 35, 100]
bmi_labels= ["<22", "22–25", "25–30", "30–35", ">35"]

cohort["age_band"] = pd.cut(cohort["age"],  bins=age_bins, labels=age_labels, right=False)
cohort["bmi_band"] = pd.cut(cohort["bmi"],  bins=bmi_bins, labels=bmi_labels, right=False)
cohort["sbp_reduction"] = cohort["sbp_baseline"] - cohort["sbp_6m"]

hm = (
    cohort.groupby(["age_band", "bmi_band"], observed=True)["sbp_reduction"]
    .mean()
    .reset_index()
    .pivot(index="age_band", columns="bmi_band", values="sbp_reduction")
)
# ensure correct order
hm = hm.reindex(index=age_labels, columns=bmi_labels)

# ── 02-rainbow-ugly.png ───────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    im = ax.imshow(hm.values, cmap="rainbow", aspect="auto")
    ax.set_xticks(range(len(bmi_labels))); ax.set_xticklabels(bmi_labels)
    ax.set_yticks(range(len(age_labels))); ax.set_yticklabels(age_labels)
    ax.set_xlabel("BMI band (kg/m²)"); ax.set_ylabel("Age band")
    for i in range(len(age_labels)):
        for j in range(len(bmi_labels)):
            val = hm.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                        fontsize=8, color="white", fontweight="bold")
    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.grid(visible=False)
    savefig(fig, DV_DIR / "02-rainbow-ugly.png", FMUP_RC)

# ── 02-sequential-good.png ────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    im = ax.imshow(hm.values, cmap="YlOrBr", aspect="auto")
    ax.set_xticks(range(len(bmi_labels))); ax.set_xticklabels(bmi_labels)
    ax.set_yticks(range(len(age_labels))); ax.set_yticklabels(age_labels)
    ax.set_xlabel("BMI band (kg/m²)"); ax.set_ylabel("Age band")
    for i in range(len(age_labels)):
        for j in range(len(bmi_labels)):
            val = hm.values[i, j]
            if not np.isnan(val):
                txt_color = "white" if val > hm.values.mean() else FMUP_DARK
                ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                        fontsize=8, color=txt_color)
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Δ SBP (mmHg)", fontsize=9)
    ax.grid(visible=False)
    savefig(fig, DV_DIR / "02-sequential-good.png", FMUP_RC)

# ── mean SBP per arm helper ────────────────────────────────────────────────────
arm_sbp = cohort.groupby("treatment")["sbp_6m"].mean()
arm_order = ["Placebo", "ACEi", "ARB", "CCB"]
arm_sbp = arm_sbp.reindex(arm_order)

# ── 03-truncated-wrong.png ────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(arm_order, arm_sbp.values, color=FMUP_BAR,
                  edgecolor=FMUP_DARK, linewidth=0.7, width=0.5)
    ax.set_ylim(132, None)
    for bar, val in zip(bars, arm_sbp.values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.3,
                f"{val:.1f}", ha="center", va="bottom", fontsize=8.5, color=FMUP_DARK)
    ax.set_xlabel("Treatment"); ax.set_ylabel("SBP at 6 months (mmHg)")
    savefig(fig, DV_DIR / "03-truncated-wrong.png", FMUP_RC)

# ── 03-honest-good.png ────────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(arm_order, arm_sbp.values, color=FMUP_BAR,
                  edgecolor=FMUP_DARK, linewidth=0.7, width=0.5)
    ax.set_ylim(0, 165)
    for bar, val in zip(bars, arm_sbp.values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 1.5,
                f"{val:.1f}", ha="center", va="bottom", fontsize=8.5, color=FMUP_DARK)
    ax.set_xlabel("Treatment"); ax.set_ylabel("SBP at 6 months (mmHg)")
    savefig(fig, DV_DIR / "03-honest-good.png", FMUP_RC)

# ── controlled pct per arm helper ─────────────────────────────────────────────
ctrl_pct = (
    cohort.groupby("treatment")["controlled_6m"]
    .apply(lambda s: 100 * s.astype(bool).mean())
    .reindex(arm_order)
)

# ── 04-3d-ugly.png ────────────────────────────────────────────────────────────
tab10 = matplotlib.colormaps["tab10"]
ugly_colors = {
    "Placebo": tab10(0),
    "ACEi":    tab10(1),
    "ARB":     tab10(2),
    "CCB":     tab10(3),
}
with plt.rc_context({}):   # matplotlib defaults
    fig, axes = plt.subplots(2, 2, figsize=(7, 6))
    for ax, arm in zip(axes.flat, arm_order):
        pct  = ctrl_pct[arm]
        rest = 100 - pct
        col  = ugly_colors[arm]
        theta = np.linspace(0, 2 * np.pi, 200)
        # inner / outer radii for donut
        for start, size, fc, label in [
            (0, pct / 100, col, f"{pct:.0f}%"),
            (pct / 100, rest / 100, "lightgray", ""),
        ]:
            angles = np.linspace(start * 2 * np.pi, (start + size) * 2 * np.pi, 100)
            r_outer = 1.0
            r_inner = 0.55
            xs_o = np.cos(angles) * r_outer
            ys_o = np.sin(angles) * r_outer
            xs_i = np.cos(angles[::-1]) * r_inner
            ys_i = np.sin(angles[::-1]) * r_inner
            from matplotlib.patches import PathPatch
            from matplotlib.path import Path as MPath
            verts = list(zip(xs_o, ys_o)) + list(zip(xs_i, ys_i)) + [(xs_o[0], ys_o[0])]
            codes = [MPath.MOVETO] + [MPath.LINETO] * (len(xs_o) - 1) + \
                    [MPath.LINETO] * len(xs_i) + [MPath.CLOSEPOLY]
            patch = PathPatch(MPath(verts, codes), facecolor=fc, edgecolor="white", linewidth=0.5)
            ax.add_patch(patch)
        ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.3, 1.3)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(arm, fontsize=10, fontweight="bold")
        ax.text(0, 0, f"{pct:.0f}%", ha="center", va="center", fontsize=13, fontweight="bold", color="white")
    plt.suptitle("% controlled at 6 months by treatment arm", fontsize=11, y=1.01)
    plt.tight_layout()
    savefig(fig, DV_DIR / "04-3d-ugly.png", {"savefig.facecolor": "white", "savefig.dpi": 150})

# ── 04-dotplot-good.png ───────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    sorted_arms = ctrl_pct.sort_values().index.tolist()
    sorted_vals = ctrl_pct[sorted_arms].values

    fig, ax = plt.subplots(figsize=(5, 3.5))
    for i, (arm, val) in enumerate(zip(sorted_arms, sorted_vals)):
        ax.hlines(i, 0, val, color="#C8CDD2", linewidth=1.5, zorder=2)
        ax.scatter(val, i, color=FMUP_DARK, s=55, zorder=3)
        ax.text(val + 0.8, i, f"{val:.0f}%", va="center", fontsize=8.5, color=FMUP_DARK)

    ax.set_yticks(range(len(sorted_arms)))
    ax.set_yticklabels(sorted_arms)
    ax.set_xlim(0, max(sorted_vals) * 1.22)
    ax.set_xlabel("Controlled at 6 months (%)")
    ax.grid(axis="x"); ax.grid(axis="y", visible=False)
    savefig(fig, DV_DIR / "04-dotplot-good.png", FMUP_RC)

# ── age_band SBP / BMI helpers ────────────────────────────────────────────────
age_band_stats = cohort.groupby("age_band", observed=True).agg(
    sbp_mean=("sbp_6m", "mean"),
    bmi_mean=("bmi",    "mean"),
).reindex(age_labels)

# ── 05-dualaxis-bad.png ───────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax2 = ax1.twinx()
    ax1.plot(age_labels, age_band_stats["sbp_mean"], color=FMUP_DARK,
             marker="o", linewidth=2, label="SBP (mmHg)")
    ax2.plot(age_labels, age_band_stats["bmi_mean"], color=FMUP4[1],
             marker="s", linewidth=2, label="BMI (kg/m²)", linestyle="--")
    ax1.set_xlabel("Age band")
    ax1.set_ylabel("SBP at 6 months (mmHg)", color=FMUP_DARK)
    ax2.set_ylabel("Mean BMI (kg/m²)", color=FMUP4[1])
    ax2.tick_params(axis="y", labelcolor=FMUP4[1])
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(FMUP4[1])
    lines1, lbls1 = ax1.get_legend_handles_labels()
    lines2, lbls2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, lbls1 + lbls2, loc="upper left", fontsize=8)
    savefig(fig, DV_DIR / "05-dualaxis-bad.png", FMUP_RC)

# ── 05-smallmult-good.png ─────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 3.5), sharey=False)
    for ax, col, title, ylabel in [
        (ax1, "sbp_mean", "SBP (mmHg)", "SBP (mmHg)"),
        (ax2, "bmi_mean", "BMI (kg/m²)", "BMI (kg/m²)"),
    ]:
        ax.plot(age_labels, age_band_stats[col], color=FMUP_DARK, marker="o", linewidth=2)
        ax.set_xlabel("Age band")
        ax.set_title(title, fontsize=10)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=15)
    plt.tight_layout()
    savefig(fig, DV_DIR / "05-smallmult-good.png", FMUP_RC)

# ── mean + SE SBP per arm helper ──────────────────────────────────────────────
arm_se = (
    cohort.groupby("treatment")["sbp_6m"]
    .agg(["mean", "sem"])
    .reindex(arm_order)
)

# ── 06-bar-mean-bad.png ───────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(arm_order, arm_se["mean"].values, color=FMUP_BAR,
                  edgecolor=FMUP_DARK, linewidth=0.7, width=0.5)
    ax.errorbar(
        x=range(len(arm_order)), y=arm_se["mean"].values, yerr=arm_se["sem"].values,
        fmt="none", ecolor=FMUP_DARK, elinewidth=1.2, capsize=5, capthick=1.2
    )
    ax.set_xlabel("Treatment"); ax.set_ylabel("SBP at 6 months (mmHg)")
    savefig(fig, DV_DIR / "06-bar-mean-bad.png", FMUP_RC)

# ── 06-distribution-good.png ──────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for arm in arm_order:
        vals = cohort[cohort["treatment"] == arm]["sbp_6m"].values
        col  = ARM_FMUP[arm]
        pos  = arm_order.index(arm)
        # strip
        jit = rng.uniform(-0.18, 0.18, len(vals))
        ax.scatter(pos + 1 + jit, vals, alpha=0.20, s=8, color=col, zorder=2)
        # box (no fill)
        bp = ax.boxplot(
            vals, positions=[pos + 1], widths=0.35, patch_artist=True, sym="",
            medianprops={"linewidth": 0},
            whiskerprops={"color": col, "linewidth": 0.8},
            capprops={"color": col, "linewidth": 0.8},
            boxprops={"facecolor": "none", "edgecolor": col, "linewidth": 0.8},
        )
        # diamond median
        ax.scatter(pos + 1, np.median(vals), marker="D", s=36, color=col, zorder=5)

    ax.set_xticks(range(1, len(arm_order) + 1))
    ax.set_xticklabels(arm_order)
    ax.set_ylabel("SBP at 6 months (mmHg)")
    savefig(fig, DV_DIR / "06-distribution-good.png", FMUP_RC)

# ── 07-spaghetti-ugly.png ────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(6, 4))
    for arm in arm_order:
        sub = traj[traj["treatment"] == arm]
        for pid in sub["id"].unique():
            row = sub[sub["id"] == pid].sort_values("month")
            ax.plot(row["month"], row["sbp"], color=ARM_FMUP[arm],
                    alpha=0.35, linewidth=0.7)
    handles = [mpatches.Patch(color=ARM_FMUP[a], label=a) for a in arm_order]
    ax.legend(handles=handles, loc="upper right")
    ax.set_xlabel("Months from baseline")
    ax.set_ylabel("SBP (mmHg)")
    ax.set_xticks([0, 1, 3, 6])
    savefig(fig, DV_DIR / "07-spaghetti-ugly.png", FMUP_RC)

# ── 07-smallmult-mean-good.png ────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.5), sharey=True)
    for ax, arm in zip(axes, arm_order):
        sub  = traj[traj["treatment"] == arm]
        col  = ARM_FMUP[arm]
        for pid in sub["id"].unique():
            row = sub[sub["id"] == pid].sort_values("month")
            ax.plot(row["month"], row["sbp"], color="#CCCCCC", alpha=0.3, linewidth=0.5, zorder=1)
        means_arm = sub.groupby("month")["sbp"].mean().reindex([0, 1, 3, 6])
        ax.plot(means_arm.index, means_arm.values, color=col, linewidth=2.2,
                marker="o", markersize=5, zorder=3)
        ax.set_title(arm, fontsize=10)
        ax.set_xticks([0, 1, 3, 6])
        ax.set_xlabel("Months")
        if ax is axes[0]:
            ax.set_ylabel("SBP (mmHg)")
    plt.tight_layout()
    savefig(fig, DV_DIR / "07-smallmult-mean-good.png", FMUP_RC)


# ══════════════════════════════════════════════════════════════════════════════
# dataviz/ chart type figures  (ch.11)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── dataviz/ chart types ─────────────────────────────────────────────────")

# ── type-01-histogram.png ─────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5.5, 4))
    sbp_vals = cohort["sbp_baseline"].values
    bins = np.arange(sbp_vals.min() - 2.5, sbp_vals.max() + 7.5, 5)
    ax.hist(sbp_vals, bins=bins, density=True,
            color=FMUP_BAR, alpha=0.70, edgecolor="white", linewidth=0.5)
    kde_x = np.linspace(sbp_vals.min(), sbp_vals.max(), 300)
    kde   = stats.gaussian_kde(sbp_vals)
    ax.plot(kde_x, kde(kde_x), color=FMUP_DARK, linewidth=2)
    ax.set_xlabel("SBP at baseline (mmHg)")
    ax.set_ylabel("Density")
    savefig(fig, DV_DIR / "type-01-histogram.png", FMUP_RC)

# ── type-02-distribution.png ──────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for arm in arm_order:
        vals = cohort[cohort["treatment"] == arm]["dbp_baseline"].values
        col  = ARM_FMUP[arm]
        pos  = arm_order.index(arm)
        # violin
        vp = ax.violinplot(vals, positions=[pos + 1], widths=0.6, showextrema=False,
                           showmedians=False)
        for body in vp["bodies"]:
            body.set_facecolor(col)
            body.set_alpha(0.18)
            body.set_edgecolor(col)
            body.set_linewidth(0.8)
        # strip
        jit = rng.uniform(-0.14, 0.14, len(vals))
        ax.scatter(pos + 1 + jit, vals, alpha=0.25, s=8, color=col, zorder=2)
        # box
        bp = ax.boxplot(
            vals, positions=[pos + 1], widths=0.28, patch_artist=True, sym="",
            medianprops={"linewidth": 0},
            whiskerprops={"color": col, "linewidth": 0.8},
            capprops={"color": col, "linewidth": 0.8},
            boxprops={"facecolor": "none", "edgecolor": col, "linewidth": 0.8},
        )
        ax.scatter(pos + 1, np.median(vals), marker="D", s=30, color=col, zorder=5)

    ax.set_xticks(range(1, len(arm_order) + 1))
    ax.set_xticklabels(arm_order)
    ax.set_ylabel("DBP at baseline (mmHg)")
    savefig(fig, DV_DIR / "type-02-distribution.png", FMUP_RC)

# ── type-03-scatter.png ───────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    x = cohort["sbp_baseline"].values
    y = cohort["dbp_baseline"].values
    ax.scatter(x, y, color=FMUP_DARK, alpha=0.30, s=12, zorder=2)
    # regression
    slope, intercept, r_val, p_val, se = stats.linregress(x, y)
    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color=FMUP4[1], linewidth=2, zorder=3)
    # CI ribbon via prediction SE
    n = len(x)
    x_bar = x.mean()
    se_y  = np.sqrt(
        np.sum((y - (slope * x + intercept))**2) / (n - 2)
        * (1/n + (x_line - x_bar)**2 / np.sum((x - x_bar)**2))
    )
    ax.fill_between(x_line, y_line - 1.96 * se_y, y_line + 1.96 * se_y,
                    color=FMUP4[1], alpha=0.15, zorder=1)
    ax.set_xlabel("SBP at baseline (mmHg)")
    ax.set_ylabel("DBP at baseline (mmHg)")
    savefig(fig, DV_DIR / "type-03-scatter.png", FMUP_RC)

# ── type-04-line.png ──────────────────────────────────────────────────────────
with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(6, 4))
    for arm in arm_order:
        sub = traj_summary[traj_summary["treatment"] == arm].sort_values("month")
        ax.plot(sub["month"], sub["sbp"], color=ARM_FMUP[arm],
                marker="o", linewidth=2, label=arm)
    ax.set_xticks([0, 1, 3, 6])
    ax.set_xlabel("Months from baseline")
    ax.set_ylabel("SBP (mmHg)")
    ax.legend(loc="upper right")
    savefig(fig, DV_DIR / "type-04-line.png", FMUP_RC)

# ── type-05-forest.png ────────────────────────────────────────────────────────
import statsmodels.formula.api as smf

cohort["treatment_cat"] = pd.Categorical(
    cohort["treatment"], categories=["Placebo", "ACEi", "ARB", "CCB"]
)
model = smf.ols("delta_sbp ~ C(treatment_cat, Treatment(reference='Placebo'))", data=cohort).fit()

forest_arms = ["ACEi", "ARB", "CCB"]
est_key   = [f"C(treatment_cat, Treatment(reference='Placebo'))[T.{a}]" for a in forest_arms]
estimates = [model.params[k]     for k in est_key]
ci_lo     = [model.conf_int().loc[k, 0] for k in est_key]
ci_hi     = [model.conf_int().loc[k, 1] for k in est_key]

with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    y_pos = range(len(forest_arms) - 1, -1, -1)
    for yp, arm, est, lo, hi in zip(y_pos, forest_arms, estimates, ci_lo, ci_hi):
        ax.hlines(yp, lo, hi, color=FMUP_DARK, linewidth=1.5)
        ax.scatter(est, yp, color=FMUP_DARK, s=80, zorder=5)
        ax.text(hi + 0.3, yp, f"{est:.1f} ({lo:.1f} – {hi:.1f})",
                va="center", fontsize=8, fontfamily="monospace", color=FMUP_DARK)
    ax.axvline(0, color=FMUP_MUTED, linewidth=1, linestyle="--", zorder=1)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(forest_arms)
    ax.set_xlabel("Δ SBP (mmHg, vs Placebo)")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x")
    savefig(fig, DV_DIR / "type-05-forest.png", FMUP_RC)

# ── type-06-km.png ────────────────────────────────────────────────────────────
from lifelines import KaplanMeierFitter

with plt.rc_context(FMUP_RC):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for arm in arm_order:
        sub = cohort_km[cohort_km["treatment"] == arm]
        kmf = KaplanMeierFitter()
        kmf.fit(sub["event_time"], sub["event"], label=arm)
        # survival = proportion NOT yet reaching control = 1 - KM controlled
        t = kmf.timeline
        sf = kmf.survival_function_[arm].values * 100  # still uncontrolled %
        ax.step(t, sf, where="post", color=ARM_FMUP[arm], linewidth=2, label=arm)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 105)
    ax.set_xlabel("Months from baseline")
    ax.set_ylabel("Uncontrolled (%)")
    ax.set_xticks([0, 1, 2, 3, 4, 5, 6])
    ax.legend(loc="upper right")
    savefig(fig, DV_DIR / "type-06-km.png", FMUP_RC)


# ══════════════════════════════════════════════════════════════════════════════
# Theme comparison
# ══════════════════════════════════════════════════════════════════════════════
print("\n── theme-comparison ──────────────────────────────────────────────────────")

def _draw_distrib_panel(ax, arm_order, colors_map, rng_ref):
    """Draw violin + box + strip of dbp_baseline by treatment on ax."""
    for arm in arm_order:
        vals = cohort[cohort["treatment"] == arm]["dbp_baseline"].values
        col  = colors_map[arm]
        pos  = arm_order.index(arm)
        # violin
        vp = ax.violinplot(vals, positions=[pos + 1], widths=0.6, showextrema=False,
                           showmedians=False)
        for body in vp["bodies"]:
            body.set_facecolor(col); body.set_alpha(0.18)
            body.set_edgecolor(col); body.set_linewidth(0.8)
        # strip
        jit = rng_ref.uniform(-0.14, 0.14, len(vals))
        ax.scatter(pos + 1 + jit, vals, alpha=0.25, s=8, color=col, zorder=2)
        # box
        bp = ax.boxplot(
            vals, positions=[pos + 1], widths=0.28, patch_artist=True, sym="",
            medianprops={"linewidth": 0},
            whiskerprops={"color": col, "linewidth": 0.8},
            capprops={"color": col, "linewidth": 0.8},
            boxprops={"facecolor": "none", "edgecolor": col, "linewidth": 0.8},
        )
        ax.scatter(pos + 1, np.median(vals), marker="D", s=28, color=col, zorder=5)

    ax.set_xticks(range(1, len(arm_order) + 1))
    ax.set_xticklabels(arm_order, fontsize=8.5)
    ax.set_ylabel("DBP at baseline (mmHg)", fontsize=9.5)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
fig.patch.set_facecolor("white")

# FMUP panel
for k, v in FMUP_RC.items():
    if k.startswith("axes.") or k in ("grid.color", "grid.linewidth", "xtick.color", "ytick.color",
                                       "xtick.labelsize", "ytick.labelsize", "axes.labelcolor",
                                       "axes.labelsize", "axes.titlesize", "text.color",
                                       "legend.fontsize", "legend.frameon"):
        try:
            plt.rcParams[k] = v
        except (KeyError, ValueError):
            pass

ax1.set_facecolor("white")
ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)
ax1.spines["bottom"].set_edgecolor("#E0E0E0"); ax1.spines["left"].set_edgecolor("#E0E0E0")
ax1.tick_params(colors="#5B6470"); ax1.yaxis.label.set_color("#1A1A1A")
ax1.xaxis.label.set_color("#1A1A1A")
ax1.grid(True, axis="y", color="#E0E0E0", linewidth=0.5)
_draw_distrib_panel(ax1, arm_order, ARM_FMUP, rng)
ax1.set_title("FMUP theme", fontsize=10, color="#1A1A1A", pad=8)

# Pequod panel
ax2.set_facecolor("#F7F3EE")
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
ax2.spines["bottom"].set_edgecolor("#BD8C68"); ax2.spines["left"].set_edgecolor("#BD8C68")
ax2.tick_params(colors="#835A49")
ax2.yaxis.label.set_color("#0D2F42"); ax2.xaxis.label.set_color("#0D2F42")
ax2.grid(True, axis="y", color="#DBC9B6", linewidth=0.5)
_draw_distrib_panel(ax2, arm_order, ARM_PEQUOD, rng)
ax2.set_title("Pequod theme", fontsize=10, color="#0D2F42", pad=8)
# Override text colors for Pequod axis
for lbl in ax2.get_xticklabels() + ax2.get_yticklabels():
    lbl.set_color("#835A49")
ax2.yaxis.label.set_color("#0D2F42")

plt.tight_layout(pad=1.5)
fig.savefig(DV_DIR / "theme-comparison.png",
            facecolor="white", bbox_inches="tight", dpi=150)
plt.close(fig)
print("  ✓ theme-comparison.png")

print("\n✓ All figures generated.")
