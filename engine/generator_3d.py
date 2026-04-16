"""
3-D geometry generator for fenestration products.

Converts a WindowModel into box primitives for the OpenGL viewport.
"""

from __future__ import annotations

from core.enums import ProductKind, WindowType
from core.models import WindowModel


class Generator3D:
    """Produces 3-D box primitives from a WindowModel."""

    def generate(self, model: WindowModel) -> list[dict]:
        if model.product_kind == ProductKind.DOOR:
            return self._generate_door(model)
        return self._generate_window(model)

    def _generate_window(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []
        w = model.width
        h = model.height
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        iw = model.inner_width
        ih = model.inner_height
        pw = model.panel_width
        mw = model.mullion_width

        shapes.append(self._box(-w / 2 + fw / 2, 0, 0, fw, h, fd, "frame"))
        shapes.append(self._box(w / 2 - fw / 2, 0, 0, fw, h, fd, "frame"))
        shapes.append(self._box(0, h / 2 - fw / 2, 0, iw, fw, fd, "frame"))
        shapes.append(self._box(0, -h / 2 + fw / 2, 0, iw, fw, fd, "frame"))

        for i in range(model.num_panels):
            px = -iw / 2 + i * (pw + mw) + pw / 2
            if model.window_type == WindowType.SLIDING:
                z_off = fd * 0.15 * (1 if i % 2 == 0 else -1)
            else:
                z_off = 0.0
            shapes.append(self._box(px, 0, z_off, pw, ih, gt, "glass"))
            if i < model.num_panels - 1:
                mx = -iw / 2 + (i + 1) * (pw + mw) - mw / 2
                shapes.append(self._box(mx, 0, 0, mw, ih, fd, "mullion"))

        return shapes

    def _generate_door(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []
        w = model.width
        h = model.height
        fw = model.frame_width
        fd = model.frame_depth
        gt = model.glass_thickness
        iw = model.inner_width
        ih = model.inner_height

        shapes.append(self._box(-w / 2 + fw / 2, 0, 0, fw, h, fd, "frame"))
        shapes.append(self._box(w / 2 - fw / 2, 0, 0, fw, h, fd, "frame"))
        shapes.append(self._box(0, h / 2 - fw / 2, 0, iw, fw, fd, "frame"))

        threshold_h = min(model.threshold_height, max(5.0, fw * 1.2))
        shapes.append(
            self._box(0, -h / 2 + fw + threshold_h / 2, 0, iw, threshold_h, fd, "threshold")
        )

        panel_depth = max(gt, 28.0)
        if model.window_type == WindowType.SINGLE_SWING_DOOR:
            shapes.append(self._box(0, 0, 0, iw - 10, ih - 10, panel_depth, "door_leaf"))
        elif model.window_type == WindowType.DOUBLE_SWING_DOOR:
            gap = max(model.mullion_width, 20.0)
            leaf_w = (iw - gap - 10) / 2
            shapes.append(self._box(-leaf_w / 2 - gap / 2, 0, 0, leaf_w, ih - 10, panel_depth, "door_leaf"))
            shapes.append(self._box(leaf_w / 2 + gap / 2, 0, 0, leaf_w, ih - 10, panel_depth, "door_leaf"))
            shapes.append(self._box(0, 0, 0, gap, ih - 10, fd, "mullion"))
        else:
            pw = model.panel_width
            mw = model.mullion_width
            for i in range(model.num_panels):
                px = -iw / 2 + i * (pw + mw) + pw / 2
                z_off = fd * 0.18 * (1 if i % 2 == 0 else -1)
                shapes.append(self._box(px, 0, z_off, pw, ih - 10, panel_depth, "door_leaf"))
                if i < model.num_panels - 1:
                    mx = -iw / 2 + (i + 1) * (pw + mw) - mw / 2
                    shapes.append(self._box(mx, 0, 0, mw, ih - 10, fd, "mullion"))

        return shapes

    @staticmethod
    def _box(x, y, z, w, h, d, layer):
        return dict(type="box", position=(x, y, z), size=(w, h, d), layer=layer)
