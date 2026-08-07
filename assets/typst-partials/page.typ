$-- Project override of the orange-book extension's page.typ partial.
$-- Identical to the upstream file except for `numbering`, which is forced to
$-- `none` here so the cover, the credits page, and the table of contents carry
$-- no folio. assets/typst-partials/typst-show.typ turns numbering back on at the
$-- start of the body, which is where a book's page numbers belong.
#set page(
  paper: $if(papersize)$"$papersize$"$else$"us-letter"$endif$,
$if(margin-geometry)$
  // Margins handled by marginalia.setup in typst-show.typ AFTER book.with()
$elseif(margin)$
  margin: ($for(margin/pairs)$$margin.key$: $margin.value$,$endfor$),
$else$
  margin: (x: 1.25in, y: 1.25in),
$endif$
  numbering: none,
  columns: $if(columns)$$columns$$else$1$endif$,
)
