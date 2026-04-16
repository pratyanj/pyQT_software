"""
Cross-section generator for horizontal and vertical cuts.

Horizontal section:
    X-axis = width, Y-axis = frame depth
Vertical section:
    X-axis = frame depth, Y-axis = product height
"""

from __future__ import annotations

from core.enums import ProductKind, WindowType
from core.models import WindowModel
from core.profile_library import get_profile, AluminiumProfilePreset, SectionFeature


class CrossSectionGenerator:
    """Produces section-view shapes from a WindowModel."""

    def generate_horizontal(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        profile = get_profile(model.profile_key)

        shapes.extend(self._frame_profile_h(0, 0, fw, fd, gt, "left", profile))
        shapes.extend(
            self._frame_profile_h(model.width - fw, 0, fw, fd, gt, "right", profile)
        )

        if model.window_type == WindowType.SLIDING and model.num_panels > 1:
            self._sliding_panels_h(shapes, model)
        else:
            self._fixed_panels_h(shapes, model)

        if model.product_kind == ProductKind.DOOR:
            label = "HORIZONTAL SECTION (DOOR)"
        else:
            label = "HORIZONTAL SECTION (WINDOW)"
        shapes.append(dict(type="text", x=model.width / 2, y=-30, text=label, layer="label"))

        self._add_section_dims_h(shapes, model)
        return shapes

    def generate_vertical(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        profile = get_profile(model.profile_key)

        shapes.extend(self._frame_profile_v(0, 0, fd, fw, gt, "top", profile))

        glass_x = (fd - gt) / 2
        glass_h = model.height - 2 * fw
        shapes.append(
            dict(
                type="rect",
                x=glass_x,
                y=fw,
                width=gt,
                height=max(glass_h, 0.0),
                layer="section_glass",
            )
        )

        if model.product_kind == ProductKind.DOOR:
            threshold_h = min(model.threshold_height, fw * 1.2)
            shapes.append(
                dict(
                    type="rect",
                    x=0,
                    y=model.height - fw - threshold_h,
                    width=fd,
                    height=threshold_h,
                    layer="threshold",
                )
            )
        else:
            shapes.extend(
                self._frame_profile_v(0, model.height - fw, fd, fw, gt, "bottom", profile)
            )

        label = (
            "VERTICAL SECTION (DOOR)"
            if model.product_kind == ProductKind.DOOR
            else "VERTICAL SECTION (WINDOW)"
        )
        shapes.append(dict(type="text", x=fd / 2, y=-30, text=label, layer="label"))

        self._add_section_dims_v(shapes, model)
        return shapes

    @classmethod
    def _frame_profile_h(
        cls,
        x: float,
        y: float,
        fw: float,
        fd: float,
        gt: float,
        side: str,
        profile: AluminiumProfilePreset | None,
    ) -> list[dict]:
        """Build a horizontal-section frame profile (jamb)."""

        shapes: list[dict] = [
            dict(type="rect", x=x, y=y, width=fw, height=fd, layer="section_frame")
        ]

        if profile and profile.horizontal_features:
            cls._append_features(
                shapes=shapes,
                features=profile.horizontal_features,
                x=x,
                y=y,
                width=fw,
                height=fd,
                mirror_x=(side == "right"),
                mirror_y=False,
            )
            return shapes

        cls._append_default_rebate_h(shapes, x, y, fw, fd, gt, side)
        return shapes

    @classmethod
    def _frame_profile_v(
        cls,
        x: float,
        y: float,
        fd: float,
        fw: float,
        gt: float,
        side: str,
        profile: AluminiumProfilePreset | None,
    ) -> list[dict]:
        """Build a vertical-section frame profile (head / sill)."""

        shapes: list[dict] = [
            dict(type="rect", x=x, y=y, width=fd, height=fw, layer="section_frame")
        ]

        if profile and profile.vertical_features:
            cls._append_features(
                shapes=shapes,
                features=profile.vertical_features,
                x=x,
                y=y,
                width=fd,
                height=fw,
                mirror_x=False,
                mirror_y=(side == "bottom"),
            )
            return shapes

        cls._append_default_rebate_v(shapes, x, y, fd, fw, gt, side)
        return shapes

    @staticmethod
    def _append_features(
        shapes: list[dict],
        features: tuple[SectionFeature, ...],
        x: float,
        y: float,
        width: float,
        height: float,
        mirror_x: bool,
        mirror_y: bool,
    ) -> None:
        for f in features:
            fx = f.x
            fy = f.y
            if mirror_x:
                fx = 1.0 - f.x - f.width
            if mirror_y:
                fy = 1.0 - f.y - f.height

            shapes.append(
                dict(
                    type="rect",
                    x=x + fx * width,
                    y=y + fy * height,
                    width=f.width * width,
                    height=f.height * height,
                    layer=f.layer,
                )
            )

    @staticmethod
    def _append_default_rebate_h(shapes, x, y, fw, fd, gt, side):
        rebate_depth = min(15.0, fw * 0.3)
        rebate_width = gt + 10

        rx = x + fw - rebate_depth if side == "left" else x
        ry = y + (fd - rebate_width) / 2
        shapes.append(
            dict(
                type="rect",
                x=rx,
                y=ry,
                width=rebate_depth,
                height=rebate_width,
                layer="rebate",
            )
        )

        gasket_h = 2.0
        for gy in (ry + 2, ry + rebate_width - gasket_h - 2):
            shapes.append(
                dict(
                    type="rect",
                    x=rx + 1,
                    y=gy,
                    width=rebate_depth - 2,
                    height=gasket_h,
                    layer="gasket",
                )
            )

    @staticmethod
    def _append_default_rebate_v(shapes, x, y, fd, fw, gt, side):
        rebate_depth = min(15.0, fw * 0.3)
        rebate_width = gt + 10

        rx = x + (fd - rebate_width) / 2
        ry = y + fw - rebate_depth if side == "top" else y
        shapes.append(
            dict(
                type="rect",
                x=rx,
                y=ry,
                width=rebate_width,
                height=rebate_depth,
                layer="rebate",
            )
        )

        gasket_w = 2.0
        for gx in (rx + 2, rx + rebate_width - gasket_w - 2):
            shapes.append(
                dict(
                    type="rect",
                    x=gx,
                    y=ry + 1,
                    width=gasket_w,
                    height=rebate_depth - 2,
                    layer="gasket",
                )
            )

    @staticmethod
    def _sliding_panels_h(shapes, model):
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        pw = model.panel_width

        track_spacing = fd / (model.num_panels + 1)
        for i in range(model.num_panels):
            track_y = track_spacing * (i + 1) - gt / 2
            px = fw + i * pw

            layer = "door_leaf" if model.product_kind == ProductKind.DOOR else "section_glass"
            shapes.append(
                dict(type="rect", x=px, y=track_y, width=pw, height=gt, layer=layer)
            )
            shapes.append(
                dict(
                    type="rect",
                    x=px,
                    y=track_y + gt + 1,
                    width=pw,
                    height=2,
                    layer="gasket",
                )
            )

    @staticmethod
    def _fixed_panels_h(shapes, model):
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        pw = model.panel_width
        glass_y = (fd - gt) / 2
        panel_layer = "door_leaf" if model.product_kind == ProductKind.DOOR else "section_glass"

        for i in range(model.num_panels):
            px = fw + i * (pw + model.mullion_width)
            shapes.append(
                dict(type="rect", x=px, y=glass_y, width=pw, height=gt, layer=panel_layer)
            )

            if i < model.num_panels - 1:
                mx = fw + (i + 1) * pw + i * model.mullion_width
                shapes.append(
                    dict(
                        type="rect",
                        x=mx,
                        y=0,
                        width=model.mullion_width,
                        height=fd,
                        layer="section_frame",
                    )
                )

    @staticmethod
    def _add_section_dims_h(shapes, model):
        dim_gap = 30
        fd = model.frame_depth

        shapes.append(
            dict(
                type="dimension",
                x1=0,
                y1=fd + dim_gap,
                x2=model.width,
                y2=fd + dim_gap,
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
                y2=fd,
                value=fd,
                unit="mm",
                orientation="vertical",
                layer="dimension",
            )
        )
        shapes.append(
            dict(
                type="dimension",
                x1=0,
                y1=-dim_gap * 0.5,
                x2=model.frame_width,
                y2=-dim_gap * 0.5,
                value=model.frame_width,
                unit="mm",
                orientation="horizontal",
                layer="dimension",
            )
        )

    @staticmethod
    def _add_section_dims_v(shapes, model):
        dim_gap = 30
        fd = model.frame_depth

        shapes.append(
            dict(
                type="dimension",
                x1=fd + dim_gap,
                y1=0,
                x2=fd + dim_gap,
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
                y1=-dim_gap * 0.5,
                x2=fd,
                y2=-dim_gap * 0.5,
                value=fd,
                unit="mm",
                orientation="horizontal",
                layer="dimension",
            )
        )
