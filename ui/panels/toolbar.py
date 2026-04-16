"""
Application toolbar – view-mode toggle, zoom buttons, file operations.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QButtonGroup, QLabel, QFrame,
)

from core.enums import ViewMode


class Toolbar(QWidget):
    """Horizontal toolbar that sits above the canvas."""

    view_changed = Signal(ViewMode)
    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    fit_view_clicked = Signal()
    save_clicked = Signal()
    load_clicked = Signal()
    export_png_clicked = Signal()
    export_pdf_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toolbar")
        self.setFixedHeight(52)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(6)

        # ── View mode toggle ────────────────────────────────────────
        self.view_group = QButtonGroup(self)
        self.view_group.setExclusive(True)

        view_modes = [
            ("🏠  Front View", ViewMode.FRONT),
            ("↔  H-Section", ViewMode.HORIZONTAL_SECTION),
            ("↕  V-Section", ViewMode.VERTICAL_SECTION),
            ("🧊  3D View", ViewMode.VIEW_3D),
        ]

        for text, mode in view_modes:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setObjectName(f"viewBtn_{mode.value}")
            btn.setMinimumWidth(110)
            btn.clicked.connect(lambda _, m=mode: self.view_changed.emit(m))
            self.view_group.addButton(btn)
            layout.addWidget(btn)
            if mode == ViewMode.FRONT:
                btn.setChecked(True)

        layout.addStretch()

        # ── Zoom controls ───────────────────────────────────────────
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(zoom_label)

        for text, signal, width in [
            ("+", self.zoom_in_clicked, 32),
            ("−", self.zoom_out_clicked, 32),
            ("Fit", self.fit_view_clicked, 42),
        ]:
            btn = QPushButton(text)
            btn.setFixedWidth(width)
            btn.clicked.connect(signal.emit)
            layout.addWidget(btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #2d3148;")
        layout.addWidget(sep)

        # ── File operations ─────────────────────────────────────────
        for text, signal in [
            ("💾 Save", self.save_clicked),
            ("📂 Open", self.load_clicked),
            ("📸 PNG", self.export_png_clicked),
            ("📄 PDF", self.export_pdf_clicked),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(signal.emit)
            layout.addWidget(btn)
