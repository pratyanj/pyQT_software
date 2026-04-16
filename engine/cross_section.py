"""
Cross-section generator for horizontal and vertical cuts through a window.

Horizontal section  – plan view (looking down, cutting at mid-height)
    X-axis = window width,  Y-axis = frame depth

Vertical section – side elevation section (looking from side, cutting at mid-width)
    X-axis = frame depth,   Y-axis = window height
"""

from __future__ import annotations

from core.models import WindowModel
from core.enums import WindowType


class CrossSectionGenerator:
    """Produces section-view shapes from a WindowModel."""

    # ── Horizontal Section ──────────────────────────────────────────

    def generate_horizontal(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        pw = model.panel_width

        # ── Left jamb profile ──────────────────────────────────────
        shapes.extend(self._frame_profile_h(0, 0, fw, fd, gt, "left"))

        # ── Glass pane(s) ──────────────────────────────────────────
        glass_y = (fd - gt) / 2  # centred in depth

        if model.num_panels == 1:
            shapes.append(
                dict(type="rect",
                     x=fw, y=glass_y,
                     width=model.inner_width, height=gt,
                     layer="section_glass")
            )
        else:
            if model.window_type == WindowType.SLIDING:
                self._sliding_panels_h(shapes, model)
            else:
                self._fixed_panels_h(shapes, model)

        # ── Right jamb profile ─────────────────────────────────────
        shapes.extend(
            self._frame_profile_h(model.width - fw, 0, fw, fd, gt, "right")
        )

        # ── Section label ──────────────────────────────────────────
        shapes.append(
            dict(type="text",
                 x=model.width / 2, y=-30,
                 text="HORIZONTAL SECTION",
                 layer="label")
        )

        # ── Dimensions ─────────────────────────────────────────────
        self._add_section_dims_h(shapes, model)

        return shapes

    # ── Vertical Section ────────────────────────────────────────────

    def generate_vertical(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness

        # ── Head (top) profile ─────────────────────────────────────
        shapes.extend(self._frame_profile_v(0, 0, fd, fw, gt, "top"))

        # ── Glass pane ─────────────────────────────────────────────
        glass_x = (fd - gt) / 2
        glass_h = model.height - 2 * fw
        shapes.append(
            dict(type="rect",
                 x=glass_x, y=fw,
                 width=gt, height=glass_h,
                 layer="section_glass")
        )

        # ── Sill (bottom) profile ─────────────────────────────────
        shapes.extend(
            self._frame_profile_v(0, model.height - fw, fd, fw, gt, "bottom")
        )

        # ── Section label ──────────────────────────────────────────
        shapes.append(
            dict(type="text",
                 x=fd / 2, y=-30,
                 text="VERTICAL SECTION",
                 layer="label")
        )

        # ── Dimensions ─────────────────────────────────────────────
        self._add_section_dims_v(shapes, model)

        return shapes

    # ── Frame profile builders ──────────────────────────────────────

    @staticmethod
    def _frame_profile_h(x, y, fw, fd, gt, side):
        """Build a horizontal-section frame profile (jamb).

        Draws the main frame body, a rebate channel, and gasket lines.
        """
        shapes = []
        rebate_depth = min(15.0, fw * 0.3)
        rebate_width = gt + 10

        # Main frame body
        shapes.append(
            dict(type="rect", x=x, y=y,
                 width=fw, height=fd,
                 layer="section_frame")
        )

        # Rebate (glass pocket) – cut into the inner face
        if side == "left":
            rx = x + fw - rebate_depth
        else:
            rx = x
        ry = y + (fd - rebate_width) / 2

        shapes.append(
            dict(type="rect", x=rx, y=ry,
                 width=rebate_depth, height=rebate_width,
                 layer="rebate")
        )

        # Gasket strips (top & bottom of glass in the rebate)
        gasket_h = 2.0
        for gy in [ry + 2, ry + rebate_width - gasket_h - 2]:
            shapes.append(
                dict(type="rect",
                     x=rx + 1, y=gy,
                     width=rebate_depth - 2, height=gasket_h,
                     layer="gasket")
            )

        return shapes

    @staticmethod
    def _frame_profile_v(x, y, fd, fw, gt, side):
        """Build a vertical-section frame profile (head / sill)."""
        shapes = []
        rebate_depth = min(15.0, fw * 0.3)
        rebate_width = gt + 10

        # Main frame body
        shapes.append(
            dict(type="rect", x=x, y=y,
                 width=fd, height=fw,
                 layer="section_frame")
        )

        # Rebate
        rx = x + (fd - rebate_width) / 2
        if side == "top":
            ry = y + fw - rebate_depth
        else:
            ry = y
        shapes.append(
            dict(type="rect", x=rx, y=ry,
                 width=rebate_width, height=rebate_depth,
                 layer="rebate")
        )

        # Gasket strips
        gasket_w = 2.0
        for gx in [rx + 2, rx + rebate_width - gasket_w - 2]:
            shapes.append(
                dict(type="rect",
                     x=gx, y=ry + 1,
                     width=gasket_w, height=rebate_depth - 2,
                     layer="gasket")
            )

        return shapes

    # ── Sliding panels (horizontal section) ─────────────────────────

    @staticmethod
    def _sliding_panels_h(shapes, model):
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        pw = model.panel_width

        track_spacing = fd / (model.num_panels + 1)

        for i in range(model.num_panels):
            # Each panel rides on its own track at a different depth
            track_y = track_spacing * (i + 1) - gt / 2
            px = fw + i * pw  # simplified: panels laid out side-by-side

            shapes.append(
                dict(type="rect",
                     x=px, y=track_y,
                     width=pw, height=gt,
                     layer="section_glass")
            )

            # Track rail indicator
            rail_h = 2
            shapes.append(
                dict(type="rect",
                     x=px, y=track_y + gt + 1,
                     width=pw, height=rail_h,
                     layer="gasket")
            )

    # ── Fixed / casement panels (horizontal section) ────────────────

    @staticmethod
    def _fixed_panels_h(shapes, model):
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        pw = model.panel_width
        glass_y = (fd - gt) / 2

        for i in range(model.num_panels):
            px = fw + i * (pw + model.mullion_width)
            shapes.append(
                dict(type="rect",
                     x=px, y=glass_y,
                     width=pw, height=gt,
                     layer="section_glass")
            )

            # Mullion profile
            if i < model.num_panels - 1:
                mx = fw + (i + 1) * pw + i * model.mullion_width
                shapes.append(
                    dict(type="rect",
                         x=mx, y=0,
                         width=model.mullion_width, height=fd,
                         layer="section_frame")
                )

    # ── Dimension helpers ───────────────────────────────────────────

    @staticmethod
    def _add_section_dims_h(shapes, model):
        dim_gap = 30
        fd = model.frame_depth

        # Overall width
        shapes.append(
            dict(type="dimension",
                 x1=0, y1=fd + dim_gap,
                 x2=model.width, y2=fd + dim_gap,
                 value=model.width, unit="mm",
                 orientation="horizontal",
                 layer="dimension")
        )
        # Frame depth
        shapes.append(
            dict(type="dimension",
                 x1=-dim_gap, y1=0,
                 x2=-dim_gap, y2=fd,
                 value=fd, unit="mm",
                 orientation="vertical",
                 layer="dimension")
        )
        # Frame width callout
        shapes.append(
            dict(type="dimension",
                 x1=0, y1=-dim_gap * 0.5,
                 x2=model.frame_width, y2=-dim_gap * 0.5,
                 value=model.frame_width, unit="mm",
                 orientation="horizontal",
                 layer="dimension")
        )

    @staticmethod
    def _add_section_dims_v(shapes, model):
        dim_gap = 30
        fd = model.frame_depth

        # Overall height
        shapes.append(
            dict(type="dimension",
                 x1=fd + dim_gap, y1=0,
                 x2=fd + dim_gap, y2=model.height,
                 value=model.height, unit="mm",
                 orientation="vertical",
                 layer="dimension")
        )
        # Frame depth
        shapes.append(
            dict(type="dimension",
                 x1=0, y1=-dim_gap * 0.5,
                 x2=fd, y2=-dim_gap * 0.5,
                 value=fd, unit="mm",
                 orientation="horizontal",
                 layer="dimension")
        )
