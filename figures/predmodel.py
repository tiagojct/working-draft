"""Generate the prediction-model figures for the TRIPOD+AI chapter (Glauca).

Fits a logistic model for 30-day readmission on the committed Part I heart-failure
cohort (figures/sw/cohort.csv), on a development split, and evaluates it on a
held-out validation split. Produces three Glauca-styled figures on the
validation set:

  figures/sw/predmodel-roc.png          ROC curve + AUC (discrimination)
  figures/sw/predmodel-calibration.png  calibration plot (decile bins + smooth)
  figures/sw/predmodel-dca.png          decision curve (net benefit)

Deterministic: the development/validation split uses a fixed seed, and the model
is a plain logistic regression, so the figures and the numbers printed at the end
reproduce byte-for-byte on a fixed numpy/pandas/statsmodels version. The printed
numbers (dev/val AUC, calibration slope/intercept, event rate) are the values
quoted in chapters/prediction-models.qmd.

Run
---
    python figures/predmodel.py
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from sklearn.metrics import roc_auc_score, roc_curve

BASE = Path(__file__).resolve().parent
OUT = BASE / "sw"
SEED = 20260515

# ── institutional font (static IBM Plex faces bundled for Typst) ────────────────
_FONT_DIR = BASE.parent / "fonts" / "glauca"
if _FONT_DIR.is_dir():
    for _ttf in _FONT_DIR.glob("IBMPlex*.ttf"):
        try:
            fm.fontManager.addfont(str(_ttf))
        except Exception:
            pass

INK, MUTED, ACCENT, GRID = "#16222a", "#55646d", "#0b62cf", "#dde6ea"
OKABE_ORANGE, OKABE_GREEN = "#D55E00", "#009E73"

GLAUCA_RC = {
    "figure.facecolor": "#ffffff", "axes.facecolor": "#ffffff",
    "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "axes.labelcolor": INK, "axes.labelsize": 9.5, "axes.titlesize": 10,
    "axes.titlecolor": INK, "text.color": INK,
    "legend.fontsize": 8.5, "legend.frameon": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["IBM Plex Sans", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.dpi": 150, "savefig.dpi": 150,
    "savefig.facecolor": "#ffffff", "savefig.pad_inches": 0.15,
}


def main() -> None:
    d = pd.read_csv(OUT / "cohort.csv").dropna(subset=["ntprobnp_discharge"]).copy()
    d["lognt"] = np.log(d["ntprobnp_discharge"] / 1000.0)
    d["male"] = (d["sex"] == "M").astype(int)
    d["y"] = d["readmit_30d"].astype(int)

    # deterministic stratified 60/40 development/validation split
    rng = np.random.default_rng(SEED)
    dev_idx = []
    for _, grp in d.groupby("y"):
        idx = grp.index.to_numpy().copy()
        rng.shuffle(idx)
        dev_idx.extend(idx[: int(0.6 * len(idx))])
    dev = d.loc[d.index.isin(dev_idx)].copy()
    val = d.loc[~d.index.isin(dev_idx)].copy()

    formula = "y ~ lognt + age + male + lvef + egfr + prior_hf_admit + afib + C(nyha_admission)"
    fit = smf.logit(formula, data=dev).fit(disp=0)
    dev["p"] = fit.predict(dev)
    val["p"] = fit.predict(val)

    auc_dev = roc_auc_score(dev["y"], dev["p"])
    auc_val = roc_auc_score(val["y"], val["p"])

    # calibration slope / intercept on validation (logistic recalibration)
    import statsmodels.api as sm
    val["lp"] = np.log(val["p"] / (1 - val["p"]))
    cal_slope = smf.logit("y ~ lp", data=val).fit(disp=0).params["lp"]
    # calibration-in-the-large: intercept of y ~ 1 with the linear predictor as offset
    citl_fit = sm.GLM(val["y"].to_numpy(), np.ones(len(val)),
                      family=sm.families.Binomial(),
                      offset=val["lp"].to_numpy()).fit()
    cal_in_the_large = float(citl_fit.params[0])
    event_rate = val["y"].mean()

    print(f"dev n={len(dev)}  val n={len(val)}")
    print(f"AUC dev={auc_dev:.3f}  val={auc_val:.3f}")
    print(f"mean predicted (val)={val['p'].mean()*100:.1f}%  observed={event_rate*100:.1f}%")
    print(f"calibration slope={cal_slope:.2f}  intercept(CITL)={cal_in_the_large:+.2f}")

    plt.rcParams.update(GLAUCA_RC)

    # ── ROC (validation) ────────────────────────────────────────────────────────
    fpr, tpr, _ = roc_curve(val["y"], val["p"])
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.plot([0, 1], [0, 1], color=MUTED, lw=0.9, ls=(0, (4, 3)))
    ax.plot(fpr, tpr, color=ACCENT, lw=2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("1 − specificity (false-positive rate)")
    ax.set_ylabel("Sensitivity (true-positive rate)")
    ax.text(0.96, 0.06, f"AUC = {auc_val:.2f}", ha="right", va="bottom",
            fontsize=10, color=INK, transform=ax.transAxes)
    ax.set_aspect("equal")
    fig.tight_layout(); fig.savefig(OUT / "predmodel-roc.png"); plt.close(fig)
    print("  ✓ predmodel-roc.png")

    # ── Calibration (validation): decile bins + smooth ──────────────────────────
    val_sorted = val.sort_values("p")
    q = pd.qcut(val_sorted["p"], 10, labels=False, duplicates="drop")
    binned = val_sorted.groupby(q).agg(pred=("p", "mean"), obs=("y", "mean"),
                                       n=("y", "size"))

    fig, ax = plt.subplots(figsize=(4.8, 4.6))
    ax.plot([0, 0.5], [0, 0.5], color=MUTED, lw=0.9, ls=(0, (4, 3)), label="Perfect")
    ax.plot(binned["pred"], binned["obs"], color=ACCENT, lw=1.4, zorder=4)
    ax.scatter(binned["pred"], binned["obs"], color=INK, s=34, zorder=5,
               label="Decile groups")
    ax.set_xlim(0, 0.5); ax.set_ylim(0, 0.5)
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.text(0.04, 0.94,
            f"slope {cal_slope:.2f}\nintercept {cal_in_the_large:+.2f}",
            transform=ax.transAxes, va="top", ha="left", fontsize=8.5, color=MUTED)
    ax.legend(loc="lower right")
    ax.set_aspect("equal")
    fig.tight_layout(); fig.savefig(OUT / "predmodel-calibration.png"); plt.close(fig)
    print("  ✓ predmodel-calibration.png")

    # ── Decision curve (validation): net benefit ────────────────────────────────
    thresholds = np.linspace(0.01, 0.40, 80)
    n = len(val)
    y = val["y"].to_numpy()
    p = val["p"].to_numpy()
    nb_model, nb_all = [], []
    for t in thresholds:
        pred_pos = p >= t
        tp = np.sum(pred_pos & (y == 1))
        fp = np.sum(pred_pos & (y == 0))
        nb_model.append(tp / n - fp / n * (t / (1 - t)))
        nb_all.append(event_rate - (1 - event_rate) * (t / (1 - t)))
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.axhline(0, color=MUTED, lw=0.9, ls=(0, (4, 3)))  # treat none
    ax.plot(thresholds, nb_all, color=OKABE_ORANGE, lw=1.6, ls="--", label="Treat all")
    ax.plot(thresholds, nb_model, color=ACCENT, lw=2, label="Model")
    ax.set_xlim(0, 0.40)
    ax.set_ylim(min(-0.02, min(nb_model) - 0.01), max(nb_model) + 0.01)
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.text(0.985, 0.04, "Treat none", transform=ax.transAxes, ha="right",
            va="bottom", fontsize=8, color=MUTED)
    ax.legend(loc="upper right")
    fig.tight_layout(); fig.savefig(OUT / "predmodel-dca.png"); plt.close(fig)
    print("  ✓ predmodel-dca.png")


if __name__ == "__main__":
    main()
