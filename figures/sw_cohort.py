"""Generate the simulated heart-failure cohort used throughout Part I.

This produces ``figures/sw/cohort.csv`` — a 5,204-patient simulated cohort of
adults hospitalised for acute heart failure, with NT-proBNP at discharge as the
exposure of interest and 30-day unplanned readmission as the primary outcome.
All examples in Chapters 2, 4, the statistical-writing chapter, and the
editorial-process chapter reference this cohort. The data are simulated for
didactic purposes only and are not derived from any real patient population.

Variables
---------
id                : int    1..5204
age               : num    years, mean ~70 (SD 12), clipped to [40, 95]
sex               : factor F / M
nyha_admission    : factor I / II / III / IV (NYHA class at admission)
lvef              : num    %, left-ventricular ejection fraction at index
egfr              : num    mL/min/1.73m^2, eGFR (CKD-EPI) at discharge
prior_hf_admit    : bool   HF admission within preceding 12 months
afib              : bool   atrial fibrillation documented during index stay
ntprobnp_discharge: num    pg/mL, lognormal; the exposure
bnp_discharge     : num    pg/mL, available for a 2,104-patient subset
readmit_30d       : bool   primary outcome (30-day unplanned readmission)
time_to_readmit   : num    days to readmission or 30 if event-free

The simulation reproduces the headline estimates referenced in the chapters
(primary adjusted OR ~1.31 for log-unit NT-proBNP, ~12% readmission rate, BNP
subset ~2,104, ~97.4% NT-proBNP availability) to within Monte Carlo noise.

Run
---
    python figures/sw_cohort.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "sw" / "cohort.csv"
N   = 5204
SEED = 20260515  # book date

rng = np.random.default_rng(SEED)

# ── baseline covariates ────────────────────────────────────────────────────────
age = np.clip(rng.normal(70, 12, N), 40, 95)
sex = rng.choice(["F", "M"], size=N, p=[0.46, 0.54])
nyha = rng.choice(["I", "II", "III", "IV"], size=N, p=[0.08, 0.42, 0.38, 0.12])
lvef = np.clip(rng.normal(42, 14, N), 15, 70)
egfr = np.clip(rng.normal(58, 22, N), 15, 120)
prior_hf = rng.binomial(1, 0.29, N).astype(bool)
afib     = rng.binomial(1, 0.34, N).astype(bool)

# ── NT-proBNP at discharge (lognormal; higher in older, lower-LVEF, prior-HF) ──
log_mu = (
    np.log(900)
    + 0.015 * (age - 70)
    - 0.012 * (lvef - 40)
    + 0.20  * prior_hf.astype(float)
    + 0.10  * afib.astype(float)
    - 0.005 * (egfr - 60)
)
ntprobnp = rng.lognormal(mean=log_mu, sigma=0.85)

# ── primary outcome (30-day readmission) ──────────────────────────────────────
# Target adjusted OR ~1.31 per log-unit NT-proBNP; base rate ~12%.
logit_p = (
    -2.30
    + 0.270 * np.log(ntprobnp / 1000.0)
    + 0.010 * (age - 70)
    - 0.008 * (lvef - 40)
    + 0.45  * prior_hf.astype(float)
    + 0.30  * (nyha == "III").astype(float)
    + 0.55  * (nyha == "IV").astype(float)
)
p_readmit = 1.0 / (1.0 + np.exp(-logit_p))
readmit = rng.binomial(1, p_readmit, N).astype(bool)

# Time to readmission within 30 days (Weibull-ish for non-event = 30).
time_to_readmit = np.where(
    readmit,
    np.clip(rng.gamma(shape=2.0, scale=6.0, size=N), 0.5, 30.0),
    30.0,
)

# ── BNP subset (n ≈ 2,104) ────────────────────────────────────────────────────
bnp_mask = rng.binomial(1, 0.404, N).astype(bool)
bnp = np.where(bnp_mask, ntprobnp / rng.uniform(5.0, 7.0, N), np.nan)

# ── induce realistic missingness for NT-proBNP (~2.6% missing) ────────────────
missing_mask = rng.binomial(1, 0.026, N).astype(bool)
ntprobnp_obs = np.where(missing_mask, np.nan, ntprobnp)

cohort = pd.DataFrame({
    "id":                 np.arange(1, N + 1),
    "age":                age.round(1),
    "sex":                sex,
    "nyha_admission":     nyha,
    "lvef":               lvef.round(1),
    "egfr":               egfr.round(1),
    "prior_hf_admit":     prior_hf,
    "afib":               afib,
    "ntprobnp_discharge": np.where(np.isnan(ntprobnp_obs), np.nan, ntprobnp_obs.round(0)),
    "bnp_discharge":      np.where(np.isnan(bnp), np.nan, bnp.round(0)),
    "readmit_30d":        readmit,
    "time_to_readmit":    time_to_readmit.round(2),
})

OUT.parent.mkdir(parents=True, exist_ok=True)
cohort.to_csv(OUT, index=False)

print(f"wrote {OUT}  (n={len(cohort)}, readmission rate={cohort['readmit_30d'].mean():.3f})")
