"""
3-D OpenGL viewport for rendering fenestration products.

Controls
--------
Left-drag     Orbit (rotate camera around the model)
Right-drag    Pan   (translate camera target)
Scroll        Zoom  (move camera closer / farther)
"""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent, QWheelEvent, QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import *   # noqa: F403
from OpenGL.GLU import *  # noqa: F403


# ── Material library ────────────────────────────────────────────────

MATERIALS = {
    "frame": {
        "ambient":   (0.42, 0.45, 0.50, 1.0),
        "diffuse":   (0.62, 0.67, 0.73, 1.0),
        "specular":  (0.88, 0.90, 0.93, 1.0),
        "shininess": 80.0,
    },
    "glass": {
        "ambient":   (0.06, 0.18, 0.30, 0.30),
        "diffuse":   (0.18, 0.50, 0.80, 0.30),
        "specular":  (0.95, 0.97, 1.00, 0.30),
        "shininess": 120.0,
    },
    "mullion": {
        "ambient":   (0.40, 0.43, 0.48, 1.0),
        "diffuse":   (0.58, 0.63, 0.68, 1.0),
        "specular":  (0.82, 0.85, 0.88, 1.0),
        "shininess": 60.0,
    },
    "door_leaf": {
        "ambient":   (0.50, 0.54, 0.58, 1.0),
        "diffuse":   (0.74, 0.79, 0.84, 1.0),
        "specular":  (0.88, 0.90, 0.93, 1.0),
        "shininess": 45.0,
    },
    "threshold": {
        "ambient":   (0.38, 0.40, 0.44, 1.0),
        "diffuse":   (0.61, 0.65, 0.70, 1.0),
        "specular":  (0.80, 0.82, 0.86, 1.0),
        "shininess": 35.0,
    },
}

# Edge colours per layer
EDGE_COLORS = {
    "frame":   (0.28, 0.30, 0.36, 1.0),
    "glass":   (0.30, 0.55, 0.85, 0.55),
    "mullion": (0.28, 0.30, 0.36, 1.0),
    "door_leaf": (0.32, 0.36, 0.42, 1.0),
    "threshold": (0.28, 0.30, 0.36, 1.0),
}


class Viewport3D(QOpenGLWidget):
    """Interactive 3-D viewport with orbit / pan / zoom."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Camera state (orbit model)
        self._azimuth: float = -30.0      # horizontal rotation (°)
        self._elevation: float = 20.0     # vertical tilt (°)
        self._distance: float = 2500.0    # eye-to-target distance
        self._target: list[float] = [0.0, 0.0, 0.0]

        # Mouse tracking
        self._last_pos: QPoint = QPoint()
        self._active_btn: Optional[Qt.MouseButton] = None

        # Scene data
        self._shapes: list[dict] = []

        self.setMinimumSize(400, 300)

    # ── Public API ──────────────────────────────────────────────────

    def set_shapes(self, shapes: list[dict]):
        self._shapes = shapes
        self.update()

    def clear(self):
        self._shapes = []
        self.update()

    def fit_to_view(self):
        """Reset camera to a sensible default based on shape extents."""
        if self._shapes:
            max_ext = 0.0
            for s in self._shapes:
                for i in range(3):
                    ext = abs(s["position"][i]) + s["size"][i] / 2
                    max_ext = max(max_ext, ext)
            self._distance = max_ext * 3.0
        else:
            self._distance = 2500.0

        self._azimuth = -30.0
        self._elevation = 20.0
        self._target = [0.0, 0.0, 0.0]
        self.update()

    # ── OpenGL lifecycle ────────────────────────────────────────────

    def initializeGL(self):
        glClearColor(0.075, 0.082, 0.11, 1.0)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)

        # Anti-aliased lines
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # ── Lighting ────────────────────────────────────────────────
        glEnable(GL_LIGHTING)

        # Key light (upper-right-front)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (1.0, 1.5, 2.0, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT,  (0.25, 0.25, 0.28, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  (0.90, 0.88, 0.85, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

        # Fill light (lower-left)
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, (-1.0, -0.3, -0.8, 0.0))
        glLightfv(GL_LIGHT1, GL_AMBIENT,  (0.08, 0.08, 0.10, 1.0))
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  (0.25, 0.28, 0.32, 1.0))
        glLightfv(GL_LIGHT1, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))

        # Rim light (behind)
        glEnable(GL_LIGHT2)
        glLightfv(GL_LIGHT2, GL_POSITION, (0.0, 0.5, -2.0, 0.0))
        glLightfv(GL_LIGHT2, GL_AMBIENT,  (0.0, 0.0, 0.0, 1.0))
        glLightfv(GL_LIGHT2, GL_DIFFUSE,  (0.15, 0.18, 0.22, 1.0))
        glLightfv(GL_LIGHT2, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))

    def resizeGL(self, w: int, h: int):
        if h == 0:
            h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / h, 1.0, 50000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # ── Camera transform (orbit) ────────────────────────────────
        glTranslatef(0, 0, -self._distance)
        glRotatef(self._elevation, 1, 0, 0)
        glRotatef(self._azimuth, 0, 1, 0)
        glTranslatef(-self._target[0], -self._target[1], -self._target[2])

        # ── Ground grid ─────────────────────────────────────────────
        self._draw_grid()

        # ── Opaque geometry (frame, mullion) ────────────────────────
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)

        for s in self._shapes:
            if s["layer"] != "glass":
                self._draw_box(s)

        glDisable(GL_POLYGON_OFFSET_FILL)

        # Edges for opaque
        for s in self._shapes:
            if s["layer"] != "glass":
                self._draw_edges(s)

        # ── Transparent geometry (glass) ────────────────────────────
        glDepthMask(GL_FALSE)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)

        for s in self._shapes:
            if s["layer"] == "glass":
                self._draw_box(s)

        glDisable(GL_POLYGON_OFFSET_FILL)

        for s in self._shapes:
            if s["layer"] == "glass":
                self._draw_edges(s)

        glDepthMask(GL_TRUE)

    # ── Internal drawing helpers ────────────────────────────────────

    def _draw_grid(self):
        """Subtle ground-plane grid underneath the model."""
        if self._shapes:
            min_y = min(s["position"][1] - s["size"][1] / 2
                        for s in self._shapes)
            max_extent = max(
                max(abs(s["position"][0]) + s["size"][0] / 2,
                    abs(s["position"][2]) + s["size"][2] / 2)
                for s in self._shapes
            )
        else:
            min_y = -500
            max_extent = 800

        y = min_y - 15
        grid = int(max_extent * 1.8)
        step = max(50, int(grid / 15))

        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        glColor4f(0.18, 0.20, 0.26, 0.45)
        for i in range(-grid, grid + 1, step):
            glVertex3f(i, y, -grid)
            glVertex3f(i, y, grid)
            glVertex3f(-grid, y, i)
            glVertex3f(grid, y, i)
        glEnd()
        glEnable(GL_LIGHTING)

    def _apply_material(self, layer: str):
        mat = MATERIALS.get(layer, MATERIALS["frame"])
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT,  mat["ambient"])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE,  mat["diffuse"])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat["specular"])
        glMaterialf(GL_FRONT_AND_BACK,  GL_SHININESS, mat["shininess"])

    def _draw_box(self, shape: dict):
        """Draw a solid box with proper normals."""
        x, y, z = shape["position"]
        w, h, d = shape["size"]
        self._apply_material(shape["layer"])

        hw, hh, hd = w / 2, h / 2, d / 2

        glBegin(GL_QUADS)

        # Front (+Z)
        glNormal3f(0, 0, 1)
        glVertex3f(x - hw, y - hh, z + hd)
        glVertex3f(x + hw, y - hh, z + hd)
        glVertex3f(x + hw, y + hh, z + hd)
        glVertex3f(x - hw, y + hh, z + hd)

        # Back (-Z)
        glNormal3f(0, 0, -1)
        glVertex3f(x + hw, y - hh, z - hd)
        glVertex3f(x - hw, y - hh, z - hd)
        glVertex3f(x - hw, y + hh, z - hd)
        glVertex3f(x + hw, y + hh, z - hd)

        # Top (+Y)
        glNormal3f(0, 1, 0)
        glVertex3f(x - hw, y + hh, z + hd)
        glVertex3f(x + hw, y + hh, z + hd)
        glVertex3f(x + hw, y + hh, z - hd)
        glVertex3f(x - hw, y + hh, z - hd)

        # Bottom (-Y)
        glNormal3f(0, -1, 0)
        glVertex3f(x - hw, y - hh, z - hd)
        glVertex3f(x + hw, y - hh, z - hd)
        glVertex3f(x + hw, y - hh, z + hd)
        glVertex3f(x - hw, y - hh, z + hd)

        # Right (+X)
        glNormal3f(1, 0, 0)
        glVertex3f(x + hw, y - hh, z + hd)
        glVertex3f(x + hw, y - hh, z - hd)
        glVertex3f(x + hw, y + hh, z - hd)
        glVertex3f(x + hw, y + hh, z + hd)

        # Left (-X)
        glNormal3f(-1, 0, 0)
        glVertex3f(x - hw, y - hh, z - hd)
        glVertex3f(x - hw, y - hh, z + hd)
        glVertex3f(x - hw, y + hh, z + hd)
        glVertex3f(x - hw, y + hh, z - hd)

        glEnd()

    def _draw_edges(self, shape: dict):
        """Draw wireframe edges for visual definition."""
        x, y, z = shape["position"]
        w, h, d = shape["size"]
        hw, hh, hd = w / 2, h / 2, d / 2

        verts = [
            (x - hw, y - hh, z - hd),  # 0  back-bottom-left
            (x + hw, y - hh, z - hd),  # 1  back-bottom-right
            (x + hw, y + hh, z - hd),  # 2  back-top-right
            (x - hw, y + hh, z - hd),  # 3  back-top-left
            (x - hw, y - hh, z + hd),  # 4  front-bottom-left
            (x + hw, y - hh, z + hd),  # 5  front-bottom-right
            (x + hw, y + hh, z + hd),  # 6  front-top-right
            (x - hw, y + hh, z + hd),  # 7  front-top-left
        ]
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # back face
            (4, 5), (5, 6), (6, 7), (7, 4),  # front face
            (0, 4), (1, 5), (2, 6), (3, 7),  # connecting
        ]

        color = EDGE_COLORS.get(shape["layer"], EDGE_COLORS["frame"])

        glDisable(GL_LIGHTING)
        glColor4f(*color)
        glLineWidth(1.4)
        glBegin(GL_LINES)
        for a, b in edges:
            glVertex3f(*verts[a])
            glVertex3f(*verts[b])
        glEnd()
        glEnable(GL_LIGHTING)

    # ── Mouse interaction ───────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        self._last_pos = event.position().toPoint()
        self._active_btn = event.button()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        dx = pos.x() - self._last_pos.x()
        dy = pos.y() - self._last_pos.y()

        if self._active_btn == Qt.MouseButton.LeftButton:
            # ── Orbit ───────────────────────────────────────────────
            self._azimuth += dx * 0.5
            self._elevation += dy * 0.5
            self._elevation = max(-89.0, min(89.0, self._elevation))

        elif self._active_btn in (Qt.MouseButton.RightButton,
                                   Qt.MouseButton.MiddleButton):
            # ── Pan ─────────────────────────────────────────────────
            scale = self._distance * 0.0012
            self._target[0] -= dx * scale
            self._target[1] += dy * scale

        self._last_pos = pos
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._active_btn = None

    def wheelEvent(self, event: QWheelEvent):
        # ── Zoom ────────────────────────────────────────────────────
        delta = event.angleDelta().y()
        factor = 0.90 if delta > 0 else 1.10
        self._distance = max(50.0, min(40000.0, self._distance * factor))
        self.update()
