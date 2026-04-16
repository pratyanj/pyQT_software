"""
Main application window – assembles toolbar, input panel, and canvas/viewport.

Orchestrates the signal flow:
    InputPanel (parameters_changed) ──→ _update_view()
    Toolbar    (view_changed)       ──→ _on_view_changed()

Uses a QStackedWidget to switch between:
    index 0 → DesignCanvas   (2-D views: front, H-section, V-section)
    index 1 → Viewport3D     (3-D OpenGL view)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QStatusBar, QFileDialog, QMessageBox,
    QStackedWidget,
)

from config.settings import APP_NAME, APP_VERSION
from core.enums import ViewMode
from core.validator import Validator
from engine.generator import FrontViewGenerator
from engine.cross_section import CrossSectionGenerator
from engine.generator_3d import Generator3D
from renderer.canvas import DesignCanvas
from renderer.viewport_3d import Viewport3D
from ui.panels.input_panel import InputPanel
from ui.panels.toolbar import Toolbar
from services.file_service import FileService
from services.export_service import ExportService


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(1200, 800)

        # State
        self._current_view = ViewMode.FRONT
        self._front_gen = FrontViewGenerator()
        self._section_gen = CrossSectionGenerator()
        self._gen_3d = Generator3D()
        self._file_svc = FileService()
        self._export_svc = ExportService()
        self._current_file: str | None = None

        self._build_ui()
        self._wire_signals()
        self._update_view()

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        self.toolbar = Toolbar()
        root.addWidget(self.toolbar)

        # Content area (splitter: left panel + stacked canvas/viewport)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.input_panel = InputPanel()
        splitter.addWidget(self.input_panel)

        # Stacked widget: 2-D canvas  (index 0)
        #                  3-D viewport (index 1)
        self._stack = QStackedWidget()

        self.canvas = DesignCanvas()
        self._stack.addWidget(self.canvas)       # index 0

        self.viewport_3d = Viewport3D()
        self._stack.addWidget(self.viewport_3d)  # index 1

        splitter.addWidget(self._stack)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(2)

        root.addWidget(splitter)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready — adjust parameters to begin")

    # ── Signal wiring ───────────────────────────────────────────────

    def _wire_signals(self):
        self.input_panel.parameters_changed.connect(self._update_view)

        self.toolbar.view_changed.connect(self._on_view_changed)
        self.toolbar.zoom_in_clicked.connect(self._zoom_in)
        self.toolbar.zoom_out_clicked.connect(self._zoom_out)
        self.toolbar.fit_view_clicked.connect(self._fit_view)
        self.toolbar.save_clicked.connect(self._save)
        self.toolbar.load_clicked.connect(self._load)
        self.toolbar.export_png_clicked.connect(self._export_png)
        self.toolbar.export_pdf_clicked.connect(self._export_pdf)

    # ── Core update loop ────────────────────────────────────────────

    def _on_view_changed(self, mode: ViewMode):
        self._current_view = mode
        self._update_view()

    def _update_view(self):
        model = self.input_panel.get_parameters()

        errors = Validator.validate(model)
        if errors:
            self._status.showMessage(f"⚠  {'; '.join(errors)}")
            return

        info = (
            f"{model.window_type.value.capitalize()}  |  "
            f"{model.width:.0f} × {model.height:.0f} mm  |  "
            f"{model.num_panels} panel(s)"
        )

        # ── 3-D view ───────────────────────────────────────────────
        if self._current_view == ViewMode.VIEW_3D:
            self._stack.setCurrentIndex(1)
            shapes_3d = self._gen_3d.generate(model)
            self.viewport_3d.set_shapes(shapes_3d)
            self._status.showMessage(
                f"3D View  —  {info}  |  "
                "Left-drag: orbit · Right-drag: pan · Scroll: zoom"
            )
            return

        # ── 2-D views ──────────────────────────────────────────────
        self._stack.setCurrentIndex(0)

        if self._current_view == ViewMode.FRONT:
            shapes = self._front_gen.generate(model)
            view_label = "Front View"
        elif self._current_view == ViewMode.HORIZONTAL_SECTION:
            shapes = self._section_gen.generate_horizontal(model)
            view_label = "Horizontal Section"
        else:
            shapes = self._section_gen.generate_vertical(model)
            view_label = "Vertical Section"

        self.canvas.draw_shapes(shapes)
        self._status.showMessage(f"{view_label}  —  {info}")

    # ── Zoom helpers (work for both 2-D and 3-D) ───────────────────

    def _zoom_in(self):
        if self._current_view == ViewMode.VIEW_3D:
            self.viewport_3d._distance *= 0.85
            self.viewport_3d.update()
        else:
            self.canvas.scale(1.25, 1.25)

    def _zoom_out(self):
        if self._current_view == ViewMode.VIEW_3D:
            self.viewport_3d._distance *= 1.15
            self.viewport_3d.update()
        else:
            self.canvas.scale(0.8, 0.8)

    def _fit_view(self):
        if self._current_view == ViewMode.VIEW_3D:
            self.viewport_3d.fit_to_view()
        else:
            self.canvas.fit_to_view()

    # ── File operations ─────────────────────────────────────────────

    _FILE_FILTER = "Fenestration Design (*.fend);;JSON Files (*.json);;All Files (*)"

    def _save(self):
        model = self.input_panel.get_parameters()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Design", self._current_file or "",
            self._FILE_FILTER,
        )
        if path:
            self._file_svc.save(model, path)
            self._current_file = path
            self._status.showMessage(f"✅  Saved → {path}")

    def _load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Design", "", self._FILE_FILTER,
        )
        if path:
            model = self._file_svc.load(path)
            if model:
                self.input_panel.set_parameters(model)
                self._current_file = path
                self._update_view()
                self._status.showMessage(f"📂  Loaded ← {path}")
            else:
                QMessageBox.warning(
                    self, "Load Error",
                    f"Could not load design from:\n{path}",
                )

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "", "PNG Images (*.png)",
        )
        if path:
            if self._current_view == ViewMode.VIEW_3D:
                img = self.viewport_3d.grabFramebuffer()
                img.save(path)
            else:
                self._export_svc.export_png(self.canvas, path)
            self._status.showMessage(f"📸  PNG exported → {path}")

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Documents (*.pdf)",
        )
        if path:
            model = self.input_panel.get_parameters()
            self._export_svc.export_pdf(self.canvas, path, model)
            self._status.showMessage(f"📄  PDF exported → {path}")
