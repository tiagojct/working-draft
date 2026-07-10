# Generated from glauca.json - do not edit by hand.
# Glauca: ggplot2 scales and theme. Source the file, then add the scales/theme to a plot.

glauca_categorical <- c("#E69F00", "#0072B2", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#F0E442")
glauca_sequential  <- c("#eaf2fc", "#c3dcf5", "#92c0ea", "#5b9edb", "#2f7cc4", "#0b5aa0", "#063a6b")
glauca_diverging   <- c("#084b96", "#3672b4", "#7ba1cd", "#c0d3e6", "#f0efe9", "#e6cdb0", "#d3a26e", "#b97435", "#8f4f16")
glauca_shapes      <- c(16, 15, 17, 18, 25, 3, 4)

.glauca_plot <- list(
  light = list(bg="#ffffff", panel="#ffffff", text="#16222a", grid="#dde6ea", muted="#55646d"),
  dark  = list(bg="#10161c", panel="#10161c", text="#e8eef2", grid="#2a3540", muted="#8c8c8c")
)

glauca_pal_d <- function(n) {
  if (n > length(glauca_categorical))
    warning("Glauca categorical has ", length(glauca_categorical), " colours; ", n, " requested.")
  unname(glauca_categorical[seq_len(n)])
}

scale_colour_glauca_d   <- function(...) ggplot2::discrete_scale("colour", "glauca", glauca_pal_d, ...)
scale_fill_glauca_d     <- function(...) ggplot2::discrete_scale("fill", "glauca", glauca_pal_d, ...)
scale_colour_glauca_c   <- function(...) ggplot2::scale_colour_gradientn(colours = glauca_sequential, ...)
scale_fill_glauca_c     <- function(...) ggplot2::scale_fill_gradientn(colours = glauca_sequential, ...)
scale_colour_glauca_div <- function(...) ggplot2::scale_colour_gradientn(colours = glauca_diverging, ...)
scale_fill_glauca_div   <- function(...) ggplot2::scale_fill_gradientn(colours = glauca_diverging, ...)
scale_color_glauca_d    <- scale_colour_glauca_d
scale_color_glauca_c    <- scale_colour_glauca_c
scale_color_glauca_div  <- scale_colour_glauca_div
scale_shape_glauca_d    <- function(...) ggplot2::scale_shape_manual(values = glauca_shapes, ...)

theme_glauca <- function(base_size = 12, base_family = "IBM Plex Sans", mode = c("light", "dark")) {
  mode <- match.arg(mode); p <- .glauca_plot[[mode]]
  ggplot2::theme_minimal(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.background  = ggplot2::element_rect(fill = p$bg, colour = NA),
      panel.background = ggplot2::element_rect(fill = p$panel, colour = NA),
      panel.grid.major = ggplot2::element_line(colour = p$grid, linewidth = 0.3),
      panel.grid.minor = ggplot2::element_blank(),
      axis.text   = ggplot2::element_text(colour = p$muted),
      axis.title  = ggplot2::element_text(colour = p$text),
      plot.title  = ggplot2::element_text(colour = p$text, family = "IBM Plex Serif"),
      plot.subtitle = ggplot2::element_text(colour = p$muted),
      legend.text  = ggplot2::element_text(colour = p$text),
      legend.title = ggplot2::element_text(colour = p$text)
    )
}
