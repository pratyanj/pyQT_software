"""
Drawing styles for each layer / element type in the rendering engine.
"""

from dataclasses import dataclass


@dataclass
class LayerStyle:
    """Visual style for a drawing layer."""
    fill_color: str
    pen_color: str
    pen_width: float = 1.5
    opacity: float = 1.0
    hatched: bool = False


# ── Layer style definitions ──────────────────────────────────────────

LAYER_STYLES: dict[str, LayerStyle] = {
    # Frame – solid aluminium look
    "frame": LayerStyle(
        fill_color="#8B9DAF",
        pen_color="#4A5568",
        pen_width=2.0,
    ),
    # Frame in section view – hatched for technical drawings
    "section_frame": LayerStyle(
        fill_color="#9FAFBF",
        pen_color="#4A5568",
        pen_width=2.0,
        hatched=True,
    ),
    # Glass – translucent blue
    "glass": LayerStyle(
        fill_color="#A8D8EA",
        pen_color="#5BA3C9",
        pen_width=1.0,
        opacity=0.75,
    ),
    # Glass in section view – solid blue
    "section_glass": LayerStyle(
        fill_color="#7EC8E3",
        pen_color="#3F9CC0",
        pen_width=1.5,
        opacity=1.0,
    ),
    # Mullion (divider between panels)
    "mullion": LayerStyle(
        fill_color="#8B9DAF",
        pen_color="#4A5568",
        pen_width=2.0,
    ),
    # Gasket / seal
    "gasket": LayerStyle(
        fill_color="#2D3748",
        pen_color="#1A202C",
        pen_width=1.0,
    ),
    # Rebate channel (glass pocket in frame)
    "rebate": LayerStyle(
        fill_color="#E8ECF1",
        pen_color="#A0AEC0",
        pen_width=0.5,
    ),
    # Dimension lines & annotations
    "dimension": LayerStyle(
        fill_color="transparent",
        pen_color="#C53030",
        pen_width=1.0,
    ),
    # Annotation arrows
    "annotation": LayerStyle(
        fill_color="transparent",
        pen_color="#2D3748",
        pen_width=1.5,
    ),
    # Section label
    "label": LayerStyle(
        fill_color="transparent",
        pen_color="#2D3748",
        pen_width=1.0,
    ),
    # Casement opening arc
    "opening_arc": LayerStyle(
        fill_color="transparent",
        pen_color="#805AD5",
        pen_width=1.5,
    ),
}
