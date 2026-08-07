// Book-specific Typst layer for The Working Draft.
//
// Loaded from `format: typst: include-in-header:` AFTER assets/glauca-typst.typ,
// so the Glauca text and heading rules are already in force. Everything here is
// emitted BEFORE `#show: book.with(...)`, which is what puts `wd-cover` and
// `wd-colophon` in scope for assets/typst-partials/typst-show.typ.

#let wd-ink   = rgb("#16222a")
#let wd-blue  = rgb("#0b62cf")
#let wd-frost = rgb("#f0f4f6")
#let wd-rule  = rgb("#cdd7dc")
#let wd-muted = rgb("#4a5b63")

// Set to a string ("10.5281/zenodo.XXXXXXX") once the Zenodo release is minted;
// see CITATION.cff and .zenodo.json. `none` keeps the line off the colophon
// rather than printing a placeholder that reads like a real identifier.
#let wd-doi = none

// Body leading is NOT set here. orange-book calls `set par(leading: 0.5em)`
// inside book(), which is nested deeper than anything in this file and would
// win; the override lives at the end of assets/typst-partials/typst-show.typ,
// inside the body scope.

// -------------------------------------------------------------- figure legends
// Captions read as apparatus rather than body copy: smaller, muted, ragged
// right, with the label carrying the weight instead of a colon. Sub-figure
// captions ("(a) ...") are rewritten by Quarto's own inner show rule inside
// quarto_super and never reach this one.
#show figure.caption: it => block(width: 100%)[
  #set text(size: 9pt, fill: wd-muted)
  #set par(justify: false, leading: 0.68em, first-line-indent: 0em)
  #align(left)[
    #text(fill: wd-ink, weight: 600)[
      #it.supplement #context it.counter.display(it.numbering)
    ]
    #h(0.45em)
    #it.body
  ]
]

// ---------------------------------------------------------------------- dates
// Quarto hands the partial an ISO date; the cover and colophon want it long.
#let wd-longdate(iso) = {
  let months = ("January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December")
  let p = str(iso).split("-")
  if p.len() >= 2 and int(p.at(1)) >= 1 and int(p.at(1)) <= 12 {
    months.at(int(p.at(1)) - 1) + " " + p.at(0)
  } else { str(iso) }
}

// ---------------------------------------------------------------------- cover
// Type-forward, matching the HTML landing hero: frost ground, one blue mark
// (the eyebrow), serif display title, imprint at the foot. No cover image.
//
// Painted into page 1's foreground (see assets/typst-partials/typst-show.typ),
// not passed to orange-book's `cover:` parameter, because orange-book draws its
// own centred title band on top of whatever `cover:` receives. The opaque frost
// ground here hides that band completely.
#let wd-cover(title: [], subtitle: [], author: "", affiliation: "", date: "") = block(
  width: 100%, height: 100%, fill: wd-frost,
  {
    place(top + left, dx: 2.6cm, dy: 3.6cm, block(width: 15.8cm, {
      text(font: "IBM Plex Mono", size: 8.5pt, weight: 500, fill: wd-blue,
           tracking: 1.9pt, upper("A field guide"))
      v(0.5cm)
      line(length: 15.8cm, stroke: 0.7pt + wd-rule)
      v(0.85cm)
      par(leading: 0.42em, justify: false,
          text(font: "IBM Plex Serif", size: 42pt, weight: 600, fill: wd-ink, title))
      v(0.6cm)
      block(width: 15.8cm,
        par(leading: 0.68em, justify: false,
            text(font: "IBM Plex Sans", size: 15pt, fill: wd-muted, subtitle)))
    }))

    place(bottom + left, dx: 2.6cm, dy: -3.2cm, block(width: 15.8cm, {
      line(length: 5.5cm, stroke: 0.7pt + wd-rule)
      v(0.5cm)
      text(font: "IBM Plex Sans", size: 11pt, weight: 600, fill: wd-ink,
           tracking: 0.9pt, upper(author))
      v(0.3cm)
      block(width: 12cm, par(leading: 0.68em, justify: false,
        text(font: "IBM Plex Sans", size: 10pt, fill: wd-muted, affiliation)))
      v(0.22cm)
      text(font: "IBM Plex Mono", size: 8.5pt, fill: wd-muted, tracking: 0.7pt,
           upper(wd-longdate(date)))
    }))
  },
)

// ------------------------------------------------------------------- colophon
// orange-book renders whatever it is handed as `copyright:` bottom-aligned on
// the page after the cover, which is exactly where a credits page belongs.
#let wd-colophon(title: [], subtitle: [], author: "", date: "") = {
  // Each entry is its own block: inside a code block, adjacent `[...]` values
  // concatenate inline, so paragraph spacing needs an explicit container.
  let entry(body) = block(width: 100%, below: 1.0em, body)

  block(width: 100%, {
    set text(size: 8.6pt, fill: wd-muted)
    set par(justify: false, leading: 0.66em, first-line-indent: 0em)
    // orange-book renders the copyright block under
    // `show link: it => [ \n #it \n ]`, and those newlines become real spaces.
    // An inner show rule does not undo it (both rules still fire), so no entry
    // below may put punctuation immediately after a link: every URL ends its
    // sentence.
    show link: it => text(fill: wd-blue, it)

    line(length: 100%, stroke: 0.7pt + wd-rule)
    v(0.5cm)

    block(width: 100%, below: 1.4em)[
      #text(font: "IBM Plex Serif", size: 11.5pt, weight: 600, fill: wd-ink, title) \
      #text(size: 9.4pt, subtitle)
    ]

    entry[First edition. Porto, #wd-longdate(date).]

    entry[
      © 2026 #author. Faculty of Medicine, University of Porto (FMUP), Portugal. \
      ORCID #link("https://orcid.org/0000-0002-7897-1101")[0000-0002-7897-1101]
    ]

    entry[
      This work is licensed under a Creative Commons
      Attribution-NonCommercial-ShareAlike 4.0 International licence
      (CC BY-NC-SA 4.0). You may copy, redistribute, and adapt it for
      non-commercial purposes provided you credit the author and license your
      derivatives under the same terms. Full terms at
      #link("https://creativecommons.org/licenses/by-nc-sa/4.0/")[creativecommons.org/licenses/by-nc-sa/4.0]
    ]

    entry[
      #text(fill: wd-ink, weight: 600)[Suggested citation.]
      Jacinto T. #title: #subtitle. Porto: Faculty of Medicine, University of
      Porto; 2026.
      #link("https://workingdraft.tiagojacinto.eu/")[workingdraft.tiagojacinto.eu]
    ]

    if wd-doi != none {
      entry[
        #text(fill: wd-ink, weight: 600)[DOI.]
        #link("https://doi.org/" + wd-doi)[#wd-doi]
      ]
    }

    entry[
      #text(fill: wd-ink, weight: 600)[Source and errata.]
      The full source of this book, including every figure script and the
      simulated cohorts, is on GitHub; corrections are welcome as issues or
      pull requests.
      #link("https://github.com/tiagojct/working-draft")[github.com/tiagojct/working-draft]
    ]

    entry[
      #text(fill: wd-ink, weight: 600)[Colophon.]
      Written in Quarto 1.10 and set with Typst 0.15. The type is IBM Plex
      Serif, IBM Plex Sans, and IBM Plex Mono, designed by Mike Abbink and Bold
      Monday for IBM and released under the SIL Open Font License. Figures were
      drawn with Matplotlib 3.11 on the Glauca design system, using the
      Okabe-Ito categorical palette.
    ]

    entry[
      #text(fill: wd-ink, weight: 600)[A note on the data.]
      Every cohort, effect estimate, table, and figure in this book is
      simulated. The heart failure and hypertension datasets were generated by
      the scripts in the repository and describe no real patients.
    ]
  })
}
