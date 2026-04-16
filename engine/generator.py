"""
Front-view shape generator.

Takes a WindowModel and produces shape dictionaries for the canvas.
"""

from __future__ import annotations

from core.enums import ProductKind, WindowType
from core.models import WindowModel


class FrontViewGenerator:
    """Generates 2-D front-view shapes for windows and doors."""

    def generate(self, model: WindowModel) -> list[dict]:
        if model.product_kind == ProductKind.DOOR:
            return self._generate_door_front(model)
        return self._generate_window_front(model)

    def _generate_window_front(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []

        fw = model.frame_width
        pw = model.panel_width

        shapes.append(
            dict(
                type="rect",
                x=0,
                y=0,
                width=model.width,
                height=model.height,
                layer="frame",
            )
        )

        for i in range(model.num_panels):
            px = fw + i * (pw + model.mullion_width)
            shapes.append(
                dict(
                    type="rect",
                    x=px,
                    y=fw,
                    width=pw,
                    height=model.inner_height,
                    layer="glass",
                )
            )

            if i < model.num_panels - 1:
                mx = fw + (i + 1) * pw + i * model.mullion_width
                shapes.append(
                    dict(
                        type="rect",
                        x=mx,
                        y=fw,
                        width=model.mullion_width,
                        height=model.inner_height,
                        layer="mullion",
                    )
                )

        if model.window_type == WindowType.SLIDING and model.num_panels >= 2:
            self._add_sliding_arrows(shapes, model)
        elif model.window_type == WindowType.CASEMENT:
            self._add_casement_arcs(shapes, model)

        self._add_dimensions(shapes, model)
        return shapes

    def _generate_door_front(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []

        fw = model.frame_width
        inner_x = fw
        inner_y = fw
        inner_w = model.inner_width
        inner_h = model.inner_height

        shapes.append(
            dict(
                type="rect",
                x=0,
                y=0,
                width=model.width,
                height=model.height,
                layer="frame",
            )
        )

        threshold_h = min(model.threshold_height, max(0.0, inner_h * 0.25))
        shapes.append(
            dict(
                type="rect",
                x=inner_x,
                y=model.height - fw - threshold_h,
                width=inner_w,
                height=threshold_h,
                layer="threshold",
            )
        )

        if model.window_type == WindowType.SINGLE_SWING_DOOR:
            self._add_single_swing_leaf(shapes, model)
        elif model.window_type == WindowType.DOUBLE_SWING_DOOR:
            self._add_double_swing_leaf(shapes, model)
        else:
            self._add_sliding_leaves(shapes, model)

        self._add_dimensions(shapes, model)

        if threshold_h > 0:
            dim_gap = 35
            y1 = model.height - fw - threshold_h
            y2 = model.height - fw
            x = model.width + dim_gap * 0.75
            shapes.append(
                dict(
                    type="dimension",
                    x1=x,
                    y1=y1,
                    x2=x,
                    y2=y2,
                    value=threshold_h,
                    unit="mm",
                    orientation="vertical",
                    layer="dimension",
                )
            )

        return shapes

    def _add_single_swing_leaf(self, shapes: list[dict], model: WindowModel):
        fw = model.frame_width
        gap = max(4.0, fw * 0.08)
        leaf_x = fw + gap
        leaf_y = fw + gap
        leaf_w = model.inner_width - 2 * gap
        leaf_h = model.inner_height - 2 * gap

        shapes.append(
            dict(
                type="rect",
                x=leaf_x,
                y=leaf_y,
                width=leaf_w,
                height=leaf_h,
                layer="door_leaf",
            )
        )
        shapes.append(
            dict(
                type="arc",
                cx=leaf_x,
                cy=leaf_y + leaf_h,
                radius=min(leaf_w, leaf_h) * 0.55,
                start_angle=270,
                span_angle=80,
                layer="opening_arc",
            )
        )

    def _add_double_swing_leaf(self, shapes: list[dict], model: WindowModel):
        fw = model.frame_width
        gap = max(4.0, fw * 0.08)
        clear_w = model.inner_width - 2 * gap
        leaf_w = (clear_w - model.mullion_width) / 2
        leaf_h = model.inner_height - 2 * gap
        y = fw + gap
        x_left = fw + gap
        x_right = x_left + leaf_w + model.mullion_width

        shapes.append(
            dict(type="rect", x=x_left, y=y, width=leaf_w, height=leaf_h, layer="door_leaf")
        )
        shapes.append(
            dict(type="rect", x=x_right, y=y, width=leaf_w, height=leaf_h, layer="door_leaf")
        )
        shapes.append(
            dict(
                type="rect",
                x=x_left + leaf_w,
                y=y,
                width=model.mullion_width,
                height=leaf_h,
                layer="mullion",
            )
        )
        radius = min(leaf_w, leaf_h) * 0.52
        shapes.append(
            dict(
                type="arc",
                cx=x_left,
                cy=y + leaf_h,
                radius=radius,
                start_angle=275,
                span_angle=70,
                layer="opening_arc",
            )
        )
        shapes.append(
            dict(
                type="arc",
                cx=x_right + leaf_w,
                cy=y + leaf_h,
                radius=radius,
                start_angle=195,
                span_angle=70,
                layer="opening_arc",
            )
        )

    def _add_sliding_leaves(self, shapes: list[dict], model: WindowModel):
        fw = model.frame_width
        pw = model.panel_width
        for i in range(model.num_panels):
            px = fw + i * (pw + model.mullion_width)
            shapes.append(
                dict(
                    type="rect",
                    x=px,
                    y=fw,
                    width=pw,
                    height=model.inner_height,
                    layer="door_leaf",
                )
            )
            if i < model.num_panels - 1:
                mx = fw + (i + 1) * pw + i * model.mullion_width
                shapes.append(
                    dict(
                        type="rect",
                        x=mx,
                        y=fw,
                        width=model.mullion_width,
                        height=model.inner_height,
                        layer="mullion",
                    )
                )
        self._add_sliding_arrows(shapes, model)

    def _add_sliding_arrows(self, shapes: list[dict], model: WindowModel):
        fw = model.frame_width
        pw = model.panel_width
        cy = fw + model.inner_height / 2

        for i in range(model.num_panels):
            cx = fw + i * (pw + model.mullion_width) + pw / 2
            direction = "right" if i % 2 == 0 else "left"
            shapes.append(
                dict(type="arrow", x=cx, y=cy, direction=direction, layer="annotation")
            )

    def _add_casement_arcs(self, shapes: list[dict], model: WindowModel):
        fw = model.frame_width
        pw = model.panel_width
        ih = model.inner_height

        for i in range(model.num_panels):
            px = fw + i * (pw + model.mullion_width)
            hinge_x = px if i % 2 == 0 else px + pw
            radius = min(pw, ih) * 0.35
            start = 0 if i % 2 == 0 else 90
            shapes.append(
                dict(
                    type="arc",
                    cx=hinge_x,
                    cy=fw + ih,
                    radius=radius,
                    start_angle=start,
                    span_angle=90,
                    layer="opening_arc",
                )
            )

    def _add_dimensions(self, shapes: list[dict], model: WindowModel):
        dim_gap = 35

        shapes.append(
            dict(
                type="dimension",
                x1=0,
                y1=model.height + dim_gap,
                x2=model.width,
                y2=model.height + dim_gap,
                value=model.width,
                unit="mm",
                orientation="horizontal",
                layer="dimension",
            )
        )
        shapes.append(
            dict(
                type="dimension",
                x1=-dim_gap,
                y1=0,
                x2=-dim_gap,
                y2=model.height,
                value=model.height,
                unit="mm",
                orientation="vertical",
                layer="dimension",
            )
        )
        shapes.append(
            dict(
                type="dimension",
                x1=0,
                y1=-dim_gap * 0.6,
                x2=model.frame_width,
                y2=-dim_gap * 0.6,
                value=model.frame_width,
                unit="mm",
                orientation="horizontal",
                layer="dimension",
            )
        )
