"""Watch-style kinematic demo case helpers."""

import matplotlib

# The generator uses Matplotlib only for off-screen contour extraction and
# review artifacts.  A desktop backend makes otherwise deterministic CAD
# generation depend on a local GUI/Tcl installation.
matplotlib.use("Agg", force=True)

from .cases import load_watch_case

__all__ = ["load_watch_case"]
