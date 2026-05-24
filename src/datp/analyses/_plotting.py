"""Shared matplotlib setup for analysis output functions.

Import ``plt`` from here instead of calling ``matplotlib.use("Agg")`` inline.
The Agg backend is set once when this module is first imported.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

__all__ = ["plt"]
