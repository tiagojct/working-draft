# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A [Quarto](https://quarto.org/) book — *The Working Draft: Writing and Data Visualisation for Health Researchers* by Tiago Jacinto (FMUP). Two parts: Part I on scientific writing, Part II on data visualisation. The audience is doctoral students and early-career health researchers. There is no application code — the source is `.qmd` (Quarto Markdown) chapters, a Python figure generator, and a custom SCSS theme.

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
```

[.github/workflows/deploy.yml](.github/workflows/deploy.yml) builds and deploys to GitHub Pages on push to `main`. [.github/workflows/check.yml](.github/workflows/check.yml) runs on every pull request: [scripts/check-refs.py](scripts/check-refs.py) first (fails the check on undefined citations or missing figure/asset paths, which `quarto render` alone lets through with exit 0), then the render, then a non-blocking lychee external-link check, then uploads `_book/` as an artifact.

## Architecture

- **[_quarto.yml](_quarto.yml) is the source of truth for chapter order and TOC.** The numeric prefix on `chapters/NN-*.qmd` is a convenience; Quarto does not infer order from the filename. A new chapter is invisible until it is added to the `book.chapters:` list in `_quarto.yml`. Unprefixed files (e.g. `ai-writing.qmd`, `statistical-writing.qmd`, `part-ii-bridge.qmd`, `guide.qmd`) are interlude/bridge chapters interleaved between the numbered ones — check `_quarto.yml` to see where each one slots in.
- **Two bibliographies.** [assets/refs-sw.bib](assets/refs-sw.bib) backs Part I (writing), [assets/refs-dataviz.bib](assets/refs-dataviz.bib) backs Part II (figures). Citations use Nature style via [assets/nature.csl](assets/nature.csl). When adding a citation, put the entry in the bib file that matches the part the chapter belongs to. Keys must be unique across the two files: pandoc/HTML dedupes silently, but the Typst PDF build fails hard on a duplicate key (a key cited from either part resolves book-wide, so define it once).
- **Margin references.** `reference-location: margin` plus the custom 700px body / 260px margin grid means citations and footnotes render in the right margin. Long content in margin notes will overflow — keep margin material short.
- **Theme is [Glauca](https://github.com/tiagojct/glauca)**, a light-first design system: IBM Plex Serif headings, IBM Plex Sans body, IBM Plex Mono code, one sky-blue mark (`#007AFF`) on a pale frost ground. Vendored into [assets/](assets/): `glauca.scss` (light/Pruina), `glauca-dark.scss` (dark/Profundum), `glauca.theme` (code highlight), `glauca-typst.typ` (PDF brand). [assets/book.scss](assets/book.scss) is the book-only layer — chiefly the type-forward landing hero, scoped to the index page via a hidden `.landing` marker and `main:has(.landing)` so chapters keep plain Glauca titles. Fonts are self-hosted: base64-inlined variable woff2 in [assets/glauca-fonts.css](assets/glauca-fonts.css) for HTML, and static IBM Plex TTFs under [fonts/glauca/](fonts/glauca/) (instantiated from the variable sources, since Typst 0.14 cannot use variable fonts) via `font-paths` for the PDF. Open Graph tags come from Quarto's built-in `open-graph`. The old FMUP extension ([_extensions/tiagojct/fmup/](_extensions/tiagojct/fmup/)) is retained but unused.
- **Figures are pre-rendered PNGs, not generated at render time.** Chapters reference files in `figures/sw/` (Part I) and `figures/dataviz/` (Part II) that are committed to the repo. To change a figure, edit and rerun [figures/generate.py](figures/generate.py), then commit the regenerated PNG(s). **The committed PNGs still use the old FMUP palette (yellow accents, Atkinson), not Glauca.** A Glauca restyle is pending: Glauca ships a matplotlib style at `glauca/dist/python/glauca.mplstyle`, but `generate.py` hard-requires the pequod package (for the ch. 14 theme-comparison figure), so a full regeneration needs pequod available and `generate.py` reworked to Glauca's palette. The ch. 14 "Theme showcase" / "Pequod in practice" content is tied to the FMUP/Pequod themes and would need rewriting too.
- **`figures/generate.py` depends on an external sibling repo.** The pequod package supplies the comparison palette. The script looks up the source via the `PEQUOD_SRC` environment variable, falling back to `~/rokovoko/pequod/python/src`; if neither is importable it raises `SystemExit` with a clear message. The FMUP theme has no pequod dependency. The script defines two rc-contexts (`FMUP_RC`, `PEQUOD_RC`) and saves under both themes for comparison figures.
- **Simulated cohorts are part of the book's didactic conceit.** Part I uses a fictional heart failure / NT-proBNP cohort generated by [figures/sw_cohort.py](figures/sw_cohort.py) → `figures/sw/cohort.csv`; Part II uses a fictional hypertension cohort generated by [figures/dv_cohort.py](figures/dv_cohort.py) → `figures/dataviz/cohort.csv`. Both scripts are deterministic for a fixed `SEED = 20260515`, but the `numpy.random.default_rng` stream and pandas' CSV float formatting drift across major versions, so a fresh run under a different environment shifts the descriptive counts by a handful of patients. The committed `figures/sw/cohort.csv` was generated with numpy 2.4.6 / pandas 3.0.3, and the Part I prose descriptives (readmission 12.8 %, NT-proBNP available 5,065/5,204, BNP subset 2,068) track that draw — reconcile prose and CSV together if you regenerate. Caveat: `figures/dataviz/cohort.csv` predates the current `dv_cohort.py` and does **not** regenerate identically; do not re-run `dv_cohort.py` over it without also reconciling the Part II numbers and figures. They are intentionally simulated for the worked examples — do not treat them as real data or suggest replacing them with a real dataset.

## Editorial conventions

- The author's voice is deliberate: terse, opinionated, second-person where it earns it. Resist softening edits ("it might be worth considering…", "in some cases…") and resist boilerplate transitions. When in doubt, match the tone of [chapters/01-why-writing.qmd](chapters/01-why-writing.qmd).
- Several recent commits (`Detrope pass`, `Address SWOT findings`) explicitly removed AI writing tropes and tightened citations — keep that in mind before adding hedges, em-dash flourishes, or "it's not just X, it's Y" constructions.
- Repo URL and `repo-actions: [edit, issue]` are wired up — chapter pages have working "Edit this page" links pointing at GitHub.
