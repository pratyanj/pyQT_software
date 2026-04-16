"""
Application-wide configuration settings for Fenestration Designer.
"""

APP_NAME = "Fenestration Designer"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Parametric window & door designer with cross-section views"

# ── Default window model values ──────────────────────────────────────
DEFAULTS = {
    "width": 1200.0,
    "height": 1000.0,
    "frame_width": 50.0,
    "frame_depth": 70.0,
    "glass_thickness": 6.0,
    "num_panels": 1,
    "mullion_width": 50.0,
}

# ── Canvas settings ──────────────────────────────────────────────────
CANVAS = {
    "background": "#F7F8FC",
    "grid_color": "#E2E6EF",
    "grid_spacing": 50,       # mm grid
    "min_zoom": -10,
    "max_zoom": 20,
    "zoom_factor": 1.15,
    "fit_margin": 60,
}

# ── Export settings ──────────────────────────────────────────────────
EXPORT = {
    "png_width": 1920,
    "png_height": 1080,
    "pdf_dpi": 300,
}
