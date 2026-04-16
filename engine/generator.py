"""
Front-view shape generator.

Takes a WindowModel and produces a list of shape dictionaries that
the renderer can draw onto the canvas.

Shape dictionary format
-----------------------
rect:
    type, x, y, width, height, layer
dimension:
    type, x1, y1, x2, y2, value, unit, layer, orientation
arrow:
    type, x, y, direction, layer
arc:
    type, cx, cy, radius, start_angle, span_angle, layer
"""

from __future__ import annotations

import math
from core.models import WindowModel
from core.enums import WindowType


class FrontViewGenerator:
    """Generates 2-D front-view shapes for a window product."""

    def generate(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []

        fw = model.frame_width
        pw = model.panel_width

        # ── Outer frame ────────────────────────────────────────────
        shapes.append(
            dict(type="rect", x=0, y=0,
                 width=model.width, height=model.height,
                 layer="frame")
        )

        # ── Glass panels & mullions ────────────────────────────────
        for i in range(model.num_panels):
            px = fw + i * (pw + model.mullion_width)
            shapes.append(
                dict(type="rect", x=px, y=fw,
                     width=pw, height=model.inner_height,
                     layer="glass")
            )

            # Mullion between panels
            if i < model.num_panels - 1:
                mx = fw + (i + 1) * pw + i * model.mullion_width
                shapes.append(
                    dict(type="rect", x=mx, y=fw,
                         width=model.mullion_width,
                         height=model.inner_height,
                         layer="mullion")
                )

        # ── Type-specific annotations ──────────────────────────────
        if model.window_type == WindowType.SLIDING and model.num_panels >= 2:
            self._add_sliding_arrows(shapes, model)
        elif model.window_type == WindowType.CASEMENT:
            self._add_casement_arcs(shapes, model)

        # ── Dimension lines ────────────────────────────────────────
        self._add_dimensions(shapes, model)

        return shapes

    # ── Private helpers ─────────────────────────────────────────────

    def _add_sliding_arrows(self, shapes: list, model: WindowModel):
        fw = model.frame_width
        pw = model.panel_width
        cy = fw + model.inner_height / 2

        for i in range(model.num_panels):
            cx = fw + i * (pw + model.mullion_width) + pw / 2
            direction = "right" if i % 2 == 0 else "left"
            shapes.append(
                dict(type="arrow", x=cx, y=cy,
                     direction=direction, layer="annotation")
            )

    def _add_casement_arcs(self, shapes: list, model: WindowModel):
        fw = model.frame_width
        pw = model.panel_width
        ih = model.inner_height

        for i in range(model.num_panels):
            px = fw + i * (pw + model.mullion_width)
            # Hinge on the near-edge, arc sweeps outward
            hinge_x = px if i % 2 == 0 else px + pw
            radius = min(pw, ih) * 0.35
            start = 0 if i % 2 == 0 else 90
            shapes.append(
                dict(type="arc",
                     cx=hinge_x, cy=fw + ih,
                     radius=radius,
                     start_angle=start, span_angle=90,
                     layer="opening_arc")
            )

    def _add_dimensions(self, shapes: list, model: WindowModel):
        dim_gap = 35

        # Horizontal – width
        shapes.append(
            dict(type="dimension",
                 x1=0, y1=model.height + dim_gap,
                 x2=model.width, y2=model.height + dim_gap,
                 value=model.width, unit="mm",
                 orientation="horizontal",
                 layer="dimension")
        )

        # Vertical – height
        shapes.append(
            dict(type="dimension",
                 x1=-dim_gap, y1=0,
                 x2=-dim_gap, y2=model.height,
                 value=model.height, unit="mm",
                 orientation="vertical",
                 layer="dimension")
        )

        # Frame width call-out (top)
        shapes.append(
            dict(type="dimension",
                 x1=0, y1=-dim_gap * 0.6,
                 x2=model.frame_width, y2=-dim_gap * 0.6,
                 value=model.frame_width, unit="mm",
                 orientation="horizontal",
                 layer="dimension")
        )
