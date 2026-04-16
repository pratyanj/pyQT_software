"""
Main application window.

Assembles toolbar, input panel, 2-D canvas, and 3-D viewport.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QStackedWidget,
)

from config.settings import APP_NAME, APP_VERSION
from core.enums import ViewMode
from core.profile_library import get_profile
from core.validator import Validator
from engine.generator import FrontViewGenerator
from engine.cross_section import CrossSectionGenerator
from engine.generator_3d import Generator3D
from renderer.canvas import DesignCanvas
from renderer.viewport_3d import Viewport3D
from services.export_service import ExportService
from services.file_service import FileService
from ui.panels.input_panel import InputPanel
from ui.panels.toolbar import Toolbar


class MainWindow(QMainWindow):
    """Top-level application window."""

    _FILE_FILTER = "Fenestration Design (*.fend);;JSON Files (*.json);;All Files (*)"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)

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

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.toolbar = Toolbar()
        root.addWidget(self.toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.input_panel = InputPanel()
        splitter.addWidget(self.input_panel)

        self._stack = QStackedWidget()
        self.canvas = DesignCanvas()
        self._stack.addWidget(self.canvas)
        self.viewport_3d = Viewport3D()
        self._stack.addWidget(self.viewport_3d)
        splitter.addWidget(self._stack)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(2)
        root.addWidget(splitter)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready - adjust parameters to begin")

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

    def _format_type_name(self, model) -> str:
        return model.window_type.value.replace("_", " ").title()

    def _format_info(self, model) -> str:
        profile_name = model.profile_key
        profile = get_profile(model.profile_key)
        if profile is not None:
            profile_name = profile.name

        return (
            f"{model.product_kind.value.title()} | "
            f"{self._format_type_name(model)} | "
            f"{model.width:.0f} x {model.height:.0f} mm | "
            f"{model.num_panels} panel(s) | "
            f"{profile_name}"
        )

    def _on_view_changed(self, mode: ViewMode):
        self._current_view = mode
        self._update_view()

    def _update_view(self):
        model = self.input_panel.get_parameters()

        errors = Validator.validate(model)
        if errors:
            self._status.showMessage(f"Validation: {'; '.join(errors)}")
            return

        info = self._format_info(model)

        if self._current_view == ViewMode.VIEW_3D:
            self._stack.setCurrentIndex(1)
            self.viewport_3d.set_shapes(self._gen_3d.generate(model))
            self._status.showMessage(
                f"3D View - {info} | Left-drag: orbit | Right-drag: pan | Scroll: zoom"
            )
            return

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
        self._status.showMessage(f"{view_label} - {info}")

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

    def _save(self):
        model = self.input_panel.get_parameters()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Design", self._current_file or "", self._FILE_FILTER
        )
        if path:
            self._file_svc.save(model, path)
            self._current_file = path
            self._status.showMessage(f"Saved -> {path}")

    def _load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Design", "", self._FILE_FILTER
        )
        if not path:
            return

        model = self._file_svc.load(path)
        if model is None:
            QMessageBox.warning(self, "Load Error", f"Could not load design from:\n{path}")
            return

        self.input_panel.set_parameters(model)
        self._current_file = path
        self._update_view()
        self._status.showMessage(f"Loaded <- {path}")

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "", "PNG Images (*.png)")
        if not path:
            return
        if self._current_view == ViewMode.VIEW_3D:
            self.viewport_3d.grabFramebuffer().save(path)
        else:
            self._export_svc.export_png(self.canvas, path)
        self._status.showMessage(f"PNG exported -> {path}")

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Documents (*.pdf)")
        if not path:
            return
        model = self.input_panel.get_parameters()
        self._export_svc.export_pdf(self.canvas, path, model)
        self._status.showMessage(f"PDF exported -> {path}")
