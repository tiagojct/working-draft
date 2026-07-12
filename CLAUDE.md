# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A [Quarto](https://quarto.org/) book — *The Working Draft: Writing and Data Visualisation for Health Researchers* by Tiago Jacinto (FMUP). Three parts: Part I on scientific writing, Part II on data visualisation, Part III on reproducible research (a TRIPOD+AI prediction-model chapter and a reproducibility/code-as-output chapter). Two appendices follow the conclusion: a [glossary](chapters/glossary.qmd) and reusable [checklists](chapters/checklists.qmd). The audience is three overlapping groups — clinical-research PhDs, health-data-science PhDs, and medical undergraduates. There is no application code — the source is `.qmd` (Quarto Markdown) chapters, Python figure scripts, and a custom SCSS theme.

## Commands

```bash
quarto preview                       # live-reload local server (use while editing)
quarto render                        # full book build (HTML + PDF) → _book/
quarto render --to typst             # PDF only (Typst) → _book/The-Working-Draft.pdf
quarto render chapters/03-clear-writing.qmd   # render a single chapter (faster iteration)
python scripts/check-refs.py         # lint: undefined citations / missing figure paths (CI gate)
python figures/sw_cohort.py          # regenerate figures/sw/cohort.csv (heart failure)
python figures/dv_cohort.py          # regenerate figures/dataviz/cohort.csv (hypertension)
python figures/generate.py           # regenerate every PNG under figures/sw/ and figures/dataviz/
python figures/meta_forest.py        # regenerate figures/sw/forest-meta.png (meta-analysis forest)
python figures/predmodel.py          # regenerate figures/sw/predmodel-{roc,calibration,dca}.png (Part III)
```

[.github/workflows/deploy.yml](.github/workflows/deploy.yml) builds and deploys to GitHub Pages on push to `main`. [.github/workflows/check.yml](.github/workflows/check.yml) runs on every pull request: [scripts/check-refs.py](scripts/check-refs.py) first (fails the check on undefined citations or missing figure/asset paths, which `quarto render` alone lets through with exit 0), then the render, then a non-blocking lychee external-link check, then uploads `_book/` as an artifact.

## Architecture

- **[_quarto.yml](_quarto.yml) is the source of truth for chapter order and TOC.** The numeric prefix on `chapters/NN-*.qmd` is a convenience; Quarto does not infer order from the filename. A new chapter is invisible until it is added to the `book.chapters:` list in `_quarto.yml`. Unprefixed files (e.g. `ai-writing.qmd`, `statistical-writing.qmd`, `part-ii-bridge.qmd`, `guide.qmd`) are interlude/bridge chapters interleaved between the numbered ones — check `_quarto.yml` to see where each one slots in.
- **Two bibliographies.** [assets/refs-sw.bib](assets/refs-sw.bib) backs Part I (writing), [assets/refs-dataviz.bib](assets/refs-dataviz.bib) backs Part II (figures). Citations use Nature style via [assets/nature.csl](assets/nature.csl). When adding a citation, put the entry in the bib file that matches the part the chapter belongs to. Keys must be unique across the two files: pandoc/HTML dedupes silently, but the Typst PDF build fails hard on a duplicate key (a key cited from either part resolves book-wide, so define it once).
- **Margin references.** `reference-location: margin` plus the custom 700px body / 260px margin grid means citations and footnotes render in the right margin. Long content in margin notes will overflow — keep margin material short.
- **Theme is [Glauca](https://github.com/tiagojct/glauca)**, a light-first design system: IBM Plex Serif headings, IBM Plex Sans body, IBM Plex Mono code, one sky-blue mark (`#007AFF`) on a pale frost ground. Vendored into [assets/](assets/): `glauca.scss` (light/Pruina), `glauca-dark.scss` (dark/Profundum), `glauca.theme` (code highlight), `glauca-typst.typ` (PDF brand). [assets/book.scss](assets/book.scss) is the book-only layer — chiefly the type-forward landing hero, scoped to the index page via a hidden `.landing` marker and `main:has(.landing)` so chapters keep plain Glauca titles. Fonts are self-hosted: base64-inlined variable woff2 in [assets/glauca-fonts.css](assets/glauca-fonts.css) for HTML, and static IBM Plex TTFs under [fonts/glauca/](fonts/glauca/) (instantiated from the variable sources, since Typst 0.14 cannot use variable fonts) via `font-paths` for the PDF. Open Graph tags come from Quarto's built-in `open-graph`. The book renders with plain Quarto `html` + `typst` formats (no custom extension).
- **Figures are pre-rendered PNGs, not generated at render time.** Chapters reference files in `figures/sw/` (Part I) and `figures/dataviz/` (Part II) that are committed to the repo. To change a figure, edit and rerun [figures/generate.py](figures/generate.py), then commit the regenerated PNG(s). All figures are styled with Glauca (IBM Plex, pale/white ground, Okabe-Ito categorical, `glauca_seq` sequential ramp); no pequod, no FMUP.
- **`figures/generate.py` is self-contained** — it has no external repo dependency. It imports the vendored [figures/glauca.py](figures/glauca.py) (palette constants + `glauca_seq`/`glauca_div` colourmaps, registered on import) with [figures/glauca.mplstyle](figures/glauca.mplstyle) as its base, and registers the static IBM Plex faces from [fonts/glauca/](fonts/glauca/) so text renders correctly even where IBM Plex is not system-installed. [figures/meta_forest.py](figures/meta_forest.py) (systematic-reviews forest plot) and [figures/predmodel.py](figures/predmodel.py) (Part III ROC/calibration/decision-curve, fit on the committed Part I cohort) use the same styling; both are deterministic and print the numbers quoted in their chapters. The R plot examples in ch. 11/12/14 use the vendored [figures/glauca.R](figures/glauca.R) (`theme_glauca()`, `scale_*_glauca_*()`).
- **Simulated cohorts are part of the book's didactic conceit.** Part I uses a fictional heart failure / NT-proBNP cohort generated by [figures/sw_cohort.py](figures/sw_cohort.py) → `figures/sw/cohort.csv`; Part II uses a fictional hypertension cohort generated by [figures/dv_cohort.py](figures/dv_cohort.py) → `figures/dataviz/cohort.csv`. Both scripts are deterministic for a fixed `SEED = 20260515`, but the `numpy.random.default_rng` stream and pandas' CSV float formatting drift across major versions, so a fresh run under a different environment shifts the descriptive counts by a handful of patients. The committed `figures/sw/cohort.csv` was generated with numpy 2.4.6 / pandas 3.0.3, and the Part I prose descriptives (readmission 12.8 %, NT-proBNP available 5,065/5,204, BNP subset 2,068) track that draw — reconcile prose and CSV together if you regenerate. Caveat: `figures/dataviz/cohort.csv` predates the current `dv_cohort.py` and does **not** regenerate identically; do not re-run `dv_cohort.py` over it without also reconciling the Part II numbers and figures. They are intentionally simulated for the worked examples — do not treat them as real data or suggest replacing them with a real dataset.

## Editorial conventions

- The author's voice is deliberate: terse, opinionated, second-person where it earns it. Resist softening edits ("it might be worth considering…", "in some cases…") and resist boilerplate transitions. When in doubt, match the tone of [chapters/01-why-writing.qmd](chapters/01-why-writing.qmd).
- Several recent commits (`Detrope pass`, `Address SWOT findings`) explicitly removed AI writing tropes and tightened citations — keep that in mind before adding hedges, em-dash flourishes, or "it's not just X, it's Y" constructions.
- Repo URL and `repo-actions: [edit, issue]` are wired up — chapter pages have working "Edit this page" links pointing at GitHub.
