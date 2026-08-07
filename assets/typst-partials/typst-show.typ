$-- Project override of the orange-book extension's typst-show.typ partial.
$-- Upstream file, plus: the Glauca cover and credits page (assets/book-typst.typ),
$-- an explicit main-color so citations and chapter rules use Glauca blue rather
$-- than Typst's default, and page numbering re-enabled at the start of the body.
$-- Keep the marginalia block in sync with the upstream partial at
$-- /Applications/quarto/share/extension-subtrees/orange-book/_extensions/orange-book/.
#import "@preview/orange-book:0.7.1": book, part, chapter, appendices

$-- orange-book's own centred title band is painted after anything passed to its
$-- `cover:` parameter, so a custom cover cannot be layered under it. Painting
$-- the Glauca cover into the page foreground of page 1 covers the band outright
$-- and leaves title/author reaching `set document()` intact for PDF metadata.
#set page(foreground: context {
  if counter(page).at(here()).first() == 1 {
    wd-cover(
      title: [$title$],
      subtitle: [$subtitle$],
      author: "$for(by-author)$$it.name.literal$$sep$, $endfor$",
      affiliation: "$for(by-author)$$for(it.affiliations)$$it.name$$sep$; $endfor$$sep$; $endfor$",
      date: "$date$",
    )
  }
})

#show: book.with(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(by-author)$
  author: "$for(by-author)$$it.name.literal$$sep$, $endfor$",
$endif$
$if(date)$
  date: "$date$",
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
  main-color: wd-blue,
  // Part dividers carry a mini-outline of the part. At orange-book's default
  // depth of 2 it lists every section too, which for Part I (16 chapters) fills
  // the whole page and collides with the placed "Part I · Writing" title and the
  // big numeral. Chapters only.
  outline-small-depth: 1,
  // orange-book's default numeral is 16em, which for "III" runs far enough right
  // to collide with the part title (placed top-right in a 60%-wide box).
  part-font-size: 7em,
  copyright: wd-colophon(
    title: [$title$],
    subtitle: [$subtitle$],
    author: "$for(by-author)$$it.name.literal$$sep$, $endfor$",
    date: "$date$",
  ),
  logo: {
    let logo-info = brand-logo.at("medium", default: none)
    if logo-info != none { image(logo-info.path, alt: logo-info.at("alt", default: none)) }
  },
$if(toc-depth)$
  outline-depth: $toc-depth$,
$endif$
$if(lof)$
$if(crossref.lof-title)$
  list-of-figure-title: "$crossref.lof-title$",
$else$
$if(quarto.language.crossref-lof-title)$
  list-of-figure-title: "$quarto.language.crossref-lof-title$",
$endif$
$endif$
$endif$
$if(lot)$
$if(crossref.lot-title)$
  list-of-table-title: "$crossref.lot-title$",
$else$
$if(quarto.language.crossref-lot-title)$
  list-of-table-title: "$quarto.language.crossref-lot-title$",
$endif$
$endif$
$endif$
$if(quarto.language.crossref-ch-prefix)$
  supplement-chapter: "$quarto.language.crossref-ch-prefix$",
$endif$
$if(margin-geometry)$
  padded-heading-number: false,
$endif$
)

$if(margin-geometry)$
// Configure marginalia page geometry for book context
// Geometry computed by Quarto's meta.lua filter (typstGeometryFromPaperWidth)
// IMPORTANT: This must come AFTER book.with() to override the book format's margin settings
#import "@preview/marginalia:0.3.1" as marginalia

#show: marginalia.setup.with(
  inner: (
    far: $margin-geometry.inner.far$,
    width: $margin-geometry.inner.width$,
    sep: $margin-geometry.inner.separation$,
  ),
  outer: (
    far: $margin-geometry.outer.far$,
    width: $margin-geometry.outer.width$,
    sep: $margin-geometry.outer.separation$,
  ),
  top: $if(margin.top)$$margin.top$$else$1.25in$endif$,
  bottom: $if(margin.bottom)$$margin.bottom$$else$1.25in$endif$,
  // CRITICAL: Enable book mode for recto/verso awareness
  book: true,
  clearance: $margin-geometry.clearance$,
)
$endif$

// Front matter (cover, credits, contents) runs unnumbered; the folio starts
// with the body. Everything below this line is the document body, so the set
// rule takes effect from the first body page onward.
#set page(numbering: $if(page-numbering)$"$page-numbering$"$else$"1"$endif$)

// Body leading. orange-book hardcodes `set par(leading: 0.5em)` inside book(),
// which gives an 11.98pt line pitch at 11pt: far too tight on a 120mm measure.
// This rule is inside book()'s body scope, so it is the nested one and wins.
// 0.75em lands the pitch near 15pt, the usual 11/15 setting for a book.
#set par(leading: 0.75em)

// orange-book hardcodes `pagebreak(to: "odd")` on every level-1 heading, so
// every chapter that ended on an odd page left a blank verso behind: 24 of them
// here, each still carrying a running head and a folio. That is a print-binding
// convention, and this PDF is a download. Drop the parity but keep the break.
//
// The replacement must be a STRONG pagebreak. With `weak: true` the break
// inside orange-book's part divider collapsed and the divider painted straight
// over the last page of the contents.
#show pagebreak: it => if it.to == "odd" { pagebreak() } else { it }

// Running heads, reimplemented. orange-book's own header prints
// "<supplement> <counter>. <body>" unconditionally, so an unnumbered chapter —
// the two Part bridges, and the preface — inherited the preceding chapter's
// number and read "Chapter 22. From figures to reproducible research". This
// version drops the number when the heading carries `numbering: none`. The two
// `state()` keys are orange-book's own; Typst states are global by key.
#set page(header: context {
  let pn = counter(page).at(here()).first()
  let appendix = state("appendix-state", none).at(here())
  set text(size: 11pt)

  // Chapter openings and part dividers carry no running head.
  if query(heading.where(level: 1)).any(h => h.location().page() == pn) { return }
  if state("part-change", false).at(here()) { return }

  if calc.odd(pn) {
    // Recto: the current section.
    let before = query(selector(heading.where(level: 2)).before(here()))
    let c = counter(heading).at(here())
    if before == () or c.len() <= 1 { return }
    let hd = before.last()
    box(width: 100%, inset: (bottom: 5pt), stroke: (bottom: 0.5pt))[
      #if hd.numbering != none {
        numbering(if appendix != none { "A.1" } else { "1.1" }, ..c.slice(0, 2))
        [ ]
      }
      #hd.body
      #h(1fr)
      #pn
    ]
  } else {
    // Verso: the current chapter.
    let before = query(selector(heading.where(level: 1)).before(here()))
    let c = counter(heading).at(here()).first()
    if before == () { return }
    let hd = before.last()
    box(width: 100%, inset: (bottom: 5pt), stroke: (bottom: 0.5pt))[
      #set par(justify: false)
      #grid(
        columns: (auto, 1fr),
        align: (left + horizon, right + horizon),
        column-gutter: 0.3em,
        [#pn],
        text(weight: "bold", if hd.numbering == none {
          hd.body
        } else if appendix != none {
          numbering("A.1", c) + ". " + hd.body
        } else {
          hd.supplement + " " + str(c) + ". " + hd.body
        }),
      )
    ]
  }
})
