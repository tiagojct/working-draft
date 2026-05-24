"""Regenerate the hypertension trial cohort used throughout Part II.

This produces ``figures/dataviz/cohort.csv`` — a 600-patient simulated cohort
from a four-arm hypertension trial (Placebo / ACEi / ARB / CCB), followed for
six months. All figures in Chapters 10–14 reference this cohort. The data are
simulated for didactic purposes only.

Variables match the table in Chapter 10:

    id, age, sex, region, bmi, comorbidities, treatment,
    sbp_baseline, dbp_baseline, follow_up_months,
    sbp_6m, dbp_6m, delta_sbp, delta_dbp,
    controlled_6m, bp_class_6m

Run
---
    python figures/dv_cohort.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT  = Path(__file__).parent / "dataviz" / "cohort.csv"
N    = 600
SEED = 20260515

rng = np.random.default_rng(SEED)

# ── covariates ────────────────────────────────────────────────────────────────
age   = np.clip(rng.normal(58, 12, N), 30, 85).round(1)
sex   = rng.choice(["F", "M"], size=N, p=[0.48, 0.52])
region = rng.choice(["North", "Centre", "South", "Islands"], size=N,
                    p=[0.32, 0.28, 0.28, 0.12])
bmi   = np.clip(rng.normal(28, 4.5, N), 18, 50).round(1)
como  = rng.poisson(1.2, N)

treatment = np.repeat(["Placebo", "ACEi", "ARB", "CCB"], N // 4)
rng.shuffle(treatment)

# ── BP at baseline ────────────────────────────────────────────────────────────
sbp_b = np.clip(rng.normal(148, 16, N), 110, 200).round(1)
dbp_b = np.clip(rng.normal(90,  10, N), 65, 120).round(1)

# Treatment-specific 6-month shifts (negative = reduction).
sbp_shift = {"Placebo": -3.0, "ACEi": -14.0, "ARB": -12.0, "CCB": -10.0}
dbp_shift = {"Placebo": -2.0, "ACEi":  -8.0, "ARB":  -7.0, "CCB":  -6.0}

s_eff = np.array([sbp_shift[t] for t in treatment])
d_eff = np.array([dbp_shift[t] for t in treatment])

sbp_6m = np.clip(sbp_b + s_eff + rng.normal(0, 6, N), 90, 200).round(1)
dbp_6m = np.clip(dbp_b + d_eff + rng.normal(0, 4, N), 55, 120).round(1)

delta_sbp = (sbp_6m - sbp_b).round(1)
delta_dbp = (dbp_6m - dbp_b).round(1)

controlled = (sbp_6m < 140) & (dbp_6m < 90)

def classify(s: float, d: float) -> str:
    if s < 120 and d < 80:
        return "Normal"
    if s < 140 and d < 90:
        return "Pre-HT"
    if s < 160 and d < 100:
        return "Stage 1"
    return "Stage 2"

bp_class = [classify(s, d) for s, d in zip(sbp_6m, dbp_6m)]

cohort = pd.DataFrame({
    "id":               np.arange(1, N + 1),
    "age":              age,
    "sex":              sex,
    "region":           region,
    "bmi":              bmi,
    "comorbidities":    como,
    "treatment":        treatment,
    "sbp_baseline":     sbp_b,
    "dbp_baseline":     dbp_b,
    "follow_up_months": 6,
    "sbp_6m":           sbp_6m,
    "dbp_6m":           dbp_6m,
    "delta_sbp":        delta_sbp,
    "delta_dbp":        delta_dbp,
    "controlled_6m":    controlled,
    "bp_class_6m":      bp_class,
})

OUT.parent.mkdir(parents=True, exist_ok=True)
cohort.to_csv(OUT, index=False, quoting=1)

print(
    f"wrote {OUT}  (n={len(cohort)}, "
    f"controlled@6m={cohort['controlled_6m'].mean():.3f})"
)
