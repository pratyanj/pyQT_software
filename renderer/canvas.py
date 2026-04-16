"""
Design canvas – a QGraphicsView with zoom, pan, grid background,
and the ability to render shape dictionaries produced by the engine.
"""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QWheelEvent,
    QMouseEvent, QPainterPath,
)
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

from renderer.styles import LAYER_STYLES, LayerStyle
from config.settings import CANVAS


class DesignCanvas(QGraphicsView):
    """Interactive canvas for rendering fenestration drawings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Rendering quality
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Interaction
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # State
        self._zoom_level: int = 0
        self._is_panning: bool = False
        self._pan_start: QPointF = QPointF()
        self._grid_spacing: int = CANVAS["grid_spacing"]

    # ── Public API ──────────────────────────────────────────────────

    def clear(self):
        self._scene.clear()

    def draw_shapes(self, shapes: list[dict]):
        """Replace scene contents with the given shapes."""
        self.clear()
        for shape in shapes:
            layer = shape.get("layer", "frame")
            style = LAYER_STYLES.get(layer, LAYER_STYLES["frame"])

            kind = shape["type"]
            if kind == "rect":
                self._draw_rect(shape, style)
            elif kind == "dimension":
                self._draw_dimension(shape, style)
            elif kind == "arrow":
                self._draw_arrow(shape, style)
            elif kind == "arc":
                self._draw_arc(shape, style)
            elif kind == "text":
                self._draw_label(shape, style)

        self.fit_to_view()

    def fit_to_view(self):
        rect = self._scene.itemsBoundingRect()
        margin = CANVAS["fit_margin"]
        rect.adjust(-margin, -margin, margin, margin)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_level = 0

    # ── Shape drawers ───────────────────────────────────────────────

    def _draw_rect(self, s: dict, st: LayerStyle):
        pen = QPen(QColor(st.pen_color), st.pen_width)
        brush = QBrush(QColor(st.fill_color))

        item = self._scene.addRect(
            s["x"], s["y"], s["width"], s["height"], pen, brush
        )
        item.setOpacity(st.opacity)

        # Hatching overlay for section views
        if st.hatched:
            self._add_hatching(s["x"], s["y"], s["width"], s["height"], st)

    def _add_hatching(self, x, y, w, h, st: LayerStyle):
        """Draw 45° diagonal hatch lines inside a rectangle."""
        pen = QPen(QColor(st.pen_color), 0.6)
        spacing = 6.0
        path = QPainterPath()

        # Lines from bottom-left to top-right
        length = w + h
        n = int(length / spacing) + 1
        for i in range(n):
            offset = i * spacing
            x1 = x + offset
            y1 = y + h
            x2 = x + offset
            y2 = y

            # Clip to rect
            lx1 = max(x, min(x + w, x1 - h))
            ly1 = y + h - max(0, min(h, x1 - x))
            lx2 = max(x, min(x + w, x1))
            ly2 = y + h - max(0, min(h, x1 - x + h))

            # Simpler approach: diagonal lines
            sx = x - h + offset
            path.moveTo(max(x, sx), min(y + h, y + h - max(0, sx - x + h) + h))

        # Use a simpler method: add many short diagonal lines
        path2 = QPainterPath()
        diag = w + h
        step = spacing
        for d in range(0, int(diag) + 1, int(step)):
            # Line from (x + d, y) to (x, y + d) clipped to rect
            x1 = x + d
            y1 = y
            x2 = x + d - h
            y2 = y + h

            # Clip to rectangle bounds
            if x1 > x + w:
                y1 = y + (x1 - (x + w))
                x1 = x + w
            if x2 < x:
                y2 = y + h - (x - x2)
                x2 = x
            if y1 < y:
                y1 = y
            if y2 > y + h:
                y2 = y + h

            if x1 >= x and x2 <= x + w and y1 >= y and y2 <= y + h:
                path2.moveTo(x1, y1)
                path2.lineTo(x2, y2)

        self._scene.addPath(path2, pen)

    def _draw_dimension(self, s: dict, st: LayerStyle):
        pen = QPen(QColor(st.pen_color), st.pen_width)
        ext_pen = QPen(QColor(st.pen_color), 0.5)
        font = QFont("Segoe UI", 7)

        x1, y1 = s["x1"], s["y1"]
        x2, y2 = s["x2"], s["y2"]
        value = s["value"]
        unit = s.get("unit", "mm")
        orient = s.get("orientation", "horizontal")

        # Main dimension line
        self._scene.addLine(x1, y1, x2, y2, pen)

        arrow = 4.0

        if orient == "horizontal":
            # Arrowheads
            self._scene.addLine(x1, y1, x1 + arrow, y1 - arrow, pen)
            self._scene.addLine(x1, y1, x1 + arrow, y1 + arrow, pen)
            self._scene.addLine(x2, y2, x2 - arrow, y2 - arrow, pen)
            self._scene.addLine(x2, y2, x2 - arrow, y2 + arrow, pen)

            # Extension lines
            self._scene.addLine(x1, y1 - 8, x1, y1 + 8, ext_pen)
            self._scene.addLine(x2, y2 - 8, x2, y2 + 8, ext_pen)
        else:
            # Vertical arrowheads
            self._scene.addLine(x1, y1, x1 - arrow, y1 + arrow, pen)
            self._scene.addLine(x1, y1, x1 + arrow, y1 + arrow, pen)
            self._scene.addLine(x2, y2, x2 - arrow, y2 - arrow, pen)
            self._scene.addLine(x2, y2, x2 + arrow, y2 - arrow, pen)

            # Extension lines
            self._scene.addLine(x1 - 8, y1, x1 + 8, y1, ext_pen)
            self._scene.addLine(x2 - 8, y2, x2 + 8, y2, ext_pen)

        # Dimension text
        text_str = f"{value:.0f} {unit}"
        text_item = self._scene.addText(text_str, font)
        text_item.setDefaultTextColor(QColor(st.pen_color))

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        br = text_item.boundingRect()

        if orient == "horizontal":
            text_item.setPos(mid_x - br.width() / 2, mid_y - br.height() - 2)
        else:
            text_item.setPos(mid_x - br.width() - 4, mid_y - br.height() / 2)

    def _draw_arrow(self, s: dict, st: LayerStyle):
        pen = QPen(QColor(st.pen_color), st.pen_width)
        x, y = s["x"], s["y"]
        direction = s.get("direction", "right")
        size = 20.0

        if direction == "right":
            self._scene.addLine(x - size, y, x + size, y, pen)
            self._scene.addLine(x + size, y, x + size - 6, y - 5, pen)
            self._scene.addLine(x + size, y, x + size - 6, y + 5, pen)
        else:
            self._scene.addLine(x - size, y, x + size, y, pen)
            self._scene.addLine(x - size, y, x - size + 6, y - 5, pen)
            self._scene.addLine(x - size, y, x - size + 6, y + 5, pen)

    def _draw_arc(self, s: dict, st: LayerStyle):
        pen = QPen(QColor(st.pen_color), st.pen_width)
        pen.setStyle(Qt.PenStyle.DashLine)
        cx, cy = s["cx"], s["cy"]
        r = s["radius"]
        start = int(s["start_angle"] * 16)
        span = int(s["span_angle"] * 16)

        self._scene.addEllipse(
            cx - r, cy - r, 2 * r, 2 * r, pen
        )

    def _draw_label(self, s: dict, st: LayerStyle):
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        item = self._scene.addText(s["text"], font)
        item.setDefaultTextColor(QColor(st.pen_color))
        br = item.boundingRect()
        item.setPos(s["x"] - br.width() / 2, s["y"] - br.height())

    # ── Background grid ─────────────────────────────────────────────

    def drawBackground(self, painter: QPainter, rect: QRectF):
        # Solid background
        painter.fillRect(rect, QColor(CANVAS["background"]))

        # Grid
        pen = QPen(QColor(CANVAS["grid_color"]), 0.5)
        painter.setPen(pen)

        gs = self._grid_spacing
        left = int(rect.left()) - (int(rect.left()) % gs)
        top = int(rect.top()) - (int(rect.top()) % gs)

        for x in range(left, int(rect.right()) + 1, gs):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()) + 1, gs):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    # ── Mouse interaction ───────────────────────────────────────────

    def wheelEvent(self, event: QWheelEvent):
        factor = CANVAS["zoom_factor"]
        if event.angleDelta().y() > 0:
            if self._zoom_level < CANVAS["max_zoom"]:
                self.scale(factor, factor)
                self._zoom_level += 1
        else:
            if self._zoom_level > CANVAS["min_zoom"]:
                self.scale(1.0 / factor, 1.0 / factor)
                self._zoom_level -= 1

    def mousePressEvent(self, event: QMouseEvent):
        if (event.button() == Qt.MouseButton.MiddleButton or
                (event.button() == Qt.MouseButton.LeftButton and
                 event.modifiers() == Qt.KeyboardModifier.ControlModifier)):
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y())
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
