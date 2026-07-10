"""Generated from glauca.json - do not edit by hand.
Glauca matplotlib colours, colormaps, and style helper."""
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.colors import LinearSegmentedColormap

GLAUCA_CATEGORICAL = ["#E69F00", "#0072B2", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#F0E442"]
GLAUCA_SEQUENTIAL  = ["#eaf2fc", "#c3dcf5", "#92c0ea", "#5b9edb", "#2f7cc4", "#0b5aa0", "#063a6b"]
GLAUCA_DIVERGING   = ["#084b96", "#3672b4", "#7ba1cd", "#c0d3e6", "#f0efe9", "#e6cdb0", "#d3a26e", "#b97435", "#8f4f16"]
GLAUCA_MARKERS     = ["o", "s", "^", "D", "v", "P", "X"]

glauca_seq = LinearSegmentedColormap.from_list("glauca_seq", GLAUCA_SEQUENTIAL)
glauca_div = LinearSegmentedColormap.from_list("glauca_div", GLAUCA_DIVERGING)
for _cm in (glauca_seq, glauca_div):
    try:
        mpl.colormaps.register(_cm)
    except (ValueError, AttributeError):
        pass

_LIGHT = dict(bg="#ffffff", panel="#ffffff", text="#16222a", grid="#dde6ea", muted="#55646d")
_DARK  = dict(bg="#10161c", panel="#10161c", text="#e8eef2", grid="#2a3540", muted="#8c8c8c")

def _apply(p):
    mpl.rcParams.update({
        "axes.prop_cycle": (cycler(color=GLAUCA_CATEGORICAL) + cycler(marker=GLAUCA_MARKERS)),
        "figure.facecolor": p["bg"], "axes.facecolor": p["panel"],
        "text.color": p["text"], "axes.labelcolor": p["text"], "axes.titlecolor": p["text"],
        "axes.edgecolor": p["muted"], "xtick.color": p["muted"], "ytick.color": p["muted"],
        "grid.color": p["grid"],
    })

def use_glauca(mode="light"):
    """Apply the Glauca style. mode='light' (default) or 'dark'."""
    plt.style.use(os.path.join(os.path.dirname(__file__), "glauca.mplstyle"))
    _apply(_DARK if mode == "dark" else _LIGHT)
