"""
Input panel - parametric controls for the product model.

All values are in millimeters. Changing any control emits
`parameters_changed` so the main window can regenerate the view.
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QGroupBox,
    QFrame,
    QScrollArea,
)

from core.enums import ProductKind, WindowType
from core.profile_library import list_profiles, get_profile, default_profile_key


class InputPanel(QWidget):
    """Left sidebar with product, profile, and dimension controls."""

    parameters_changed = Signal()

    _WINDOW_TYPES = (
        WindowType.FIXED,
        WindowType.SLIDING,
        WindowType.CASEMENT,
    )
    _DOOR_TYPES = (
        WindowType.SINGLE_SWING_DOOR,
        WindowType.DOUBLE_SWING_DOOR,
        WindowType.SLIDING,
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InputPanel")
        self.setFixedWidth(330)
        self._suspend_emits = False
        self._setup_ui()
        self._on_product_changed()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(14)

        header = QLabel("Parameters")
        header.setStyleSheet(
            "font-size: 17px; font-weight: 700; color: #E2E8F0; padding-bottom: 4px;"
        )
        layout.addWidget(header)

        product_group = self._group("Product Setup")
        pl = QFormLayout()
        pl.setSpacing(10)

        self.product_combo = QComboBox()
        self.product_combo.addItem("Window", ProductKind.WINDOW)
        self.product_combo.addItem("Door", ProductKind.DOOR)
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        pl.addRow("Product:", self.product_combo)

        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        pl.addRow("Design Type:", self.type_combo)

        self.panels_spin = QSpinBox()
        self.panels_spin.setRange(1, 6)
        self.panels_spin.setValue(1)
        self.panels_spin.valueChanged.connect(lambda _: self._emit_parameters_changed())
        pl.addRow("Panels:", self.panels_spin)

        product_group.setLayout(pl)
        layout.addWidget(product_group)

        profile_group = self._group("Aluminium Profile")
        pfl = QFormLayout()
        pfl.setSpacing(10)

        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        pfl.addRow("Series:", self.profile_combo)

        self.profile_info = QLabel("-")
        self.profile_info.setWordWrap(True)
        self.profile_info.setStyleSheet("color: #A0AEC0; font-size: 11px;")
        pfl.addRow("Spec:", self.profile_info)

        self.profile_source = QLabel("Add custom profiles in config/custom_profiles.json")
        self.profile_source.setWordWrap(True)
        self.profile_source.setStyleSheet("color: #718096; font-size: 10px;")
        pfl.addRow("Source:", self.profile_source)

        profile_group.setLayout(pfl)
        layout.addWidget(profile_group)

        dim_group = self._group("Dimensions")
        dl = QFormLayout()
        dl.setSpacing(10)

        self.width_spin = self._spin(300, 7000, 1200, 10)
        dl.addRow("Width:", self.width_spin)

        self.height_spin = self._spin(300, 7000, 1000, 10)
        dl.addRow("Height:", self.height_spin)

        dim_group.setLayout(dl)
        layout.addWidget(dim_group)

        frame_group = self._group("Frame Profile")
        fl = QFormLayout()
        fl.setSpacing(10)

        self.frame_width_spin = self._spin(20, 250, 50, 5)
        fl.addRow("Frame Width:", self.frame_width_spin)

        self.frame_depth_spin = self._spin(30, 250, 70, 5)
        fl.addRow("Frame Depth:", self.frame_depth_spin)

        self.mullion_spin = self._spin(10, 200, 50, 5)
        fl.addRow("Mullion:", self.mullion_spin)

        self.threshold_spin = self._spin(0, 120, 25, 2.5)
        fl.addRow("Threshold:", self.threshold_spin)

        frame_group.setLayout(fl)
        layout.addWidget(frame_group)

        glass_group = self._group("Glass")
        gl = QFormLayout()
        gl.setSpacing(10)

        self.glass_spin = self._spin(3, 50, 6, 1)
        gl.addRow("Thickness:", self.glass_spin)

        glass_group.setLayout(gl)
        layout.addWidget(glass_group)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _group(self, title: str) -> QGroupBox:
        return QGroupBox(title)

    def _spin(self, lo, hi, default, step) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setValue(default)
        s.setSingleStep(step)
        s.setDecimals(1)
        s.setSuffix(" mm")
        s.valueChanged.connect(lambda _: self._emit_parameters_changed())
        return s

    def _emit_parameters_changed(self):
        if not self._suspend_emits:
            self.parameters_changed.emit()

    def _suspend(self):
        class _SuspendContext:
            def __init__(self, panel: "InputPanel"):
                self._panel = panel
                self._previous = panel._suspend_emits

            def __enter__(self):
                self._panel._suspend_emits = True

            def __exit__(self, exc_type, exc, tb):
                self._panel._suspend_emits = self._previous

        return _SuspendContext(self)

    def _friendly_type_name(self, wtype: WindowType) -> str:
        mapping = {
            WindowType.FIXED: "Fixed",
            WindowType.SLIDING: "Sliding",
            WindowType.CASEMENT: "Casement",
            WindowType.SINGLE_SWING_DOOR: "Single Swing",
            WindowType.DOUBLE_SWING_DOOR: "Double Swing",
        }
        return mapping.get(wtype, wtype.value.replace("_", " ").title())

    def _valid_types_for_product(self, kind: ProductKind) -> tuple[WindowType, ...]:
        return self._WINDOW_TYPES if kind == ProductKind.WINDOW else self._DOOR_TYPES

    def _on_product_changed(self):
        with self._suspend():
            product_kind = self.product_combo.currentData()

            current_type = self.type_combo.currentData()
            valid_types = self._valid_types_for_product(product_kind)
            self.type_combo.clear()
            for wtype in valid_types:
                self.type_combo.addItem(self._friendly_type_name(wtype), wtype)

            idx = self.type_combo.findData(current_type)
            self.type_combo.setCurrentIndex(max(idx, 0))

            if product_kind == ProductKind.DOOR:
                self.height_spin.setMinimum(1700.0)
                if self.height_spin.value() < 1700.0:
                    self.height_spin.setValue(2100.0)
                self.width_spin.setMinimum(600.0)
                self.threshold_spin.setEnabled(True)
            else:
                self.height_spin.setMinimum(300.0)
                self.width_spin.setMinimum(300.0)
                self.threshold_spin.setEnabled(False)

            self._refresh_profiles()
            self._set_panel_rules()
            self._apply_current_profile()
        self._emit_parameters_changed()

    def _on_type_changed(self):
        with self._suspend():
            self._set_panel_rules()
            self._refresh_profiles()
        self._emit_parameters_changed()

    def _on_profile_changed(self):
        with self._suspend():
            self._apply_current_profile()
        self._emit_parameters_changed()

    def _set_panel_rules(self):
        product_kind = self.product_combo.currentData()
        wtype = self.type_combo.currentData()

        if product_kind == ProductKind.WINDOW:
            if wtype == WindowType.SLIDING:
                self.panels_spin.setRange(2, 6)
                if self.panels_spin.value() < 2:
                    self.panels_spin.setValue(2)
            else:
                self.panels_spin.setRange(1, 6)
        else:
            if wtype == WindowType.SINGLE_SWING_DOOR:
                self.panels_spin.setRange(1, 1)
                self.panels_spin.setValue(1)
            elif wtype == WindowType.DOUBLE_SWING_DOOR:
                self.panels_spin.setRange(2, 2)
                self.panels_spin.setValue(2)
            elif wtype == WindowType.SLIDING:
                self.panels_spin.setRange(2, 6)
                if self.panels_spin.value() < 2:
                    self.panels_spin.setValue(2)

    def _refresh_profiles(self):
        product_kind = self.product_combo.currentData()
        wtype = self.type_combo.currentData()
        presets = list_profiles(product_kind=product_kind, window_type=wtype)
        if not presets:
            presets = list_profiles(product_kind=product_kind)

        current_key = self.profile_combo.currentData()
        self.profile_combo.clear()
        for preset in presets:
            self.profile_combo.addItem(preset.name, preset.key)

        idx = self.profile_combo.findData(current_key)
        if idx < 0:
            fallback = default_profile_key(product_kind)
            idx = self.profile_combo.findData(fallback)
        if idx < 0 and self.profile_combo.count() > 0:
            idx = 0
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)

    def _apply_current_profile(self):
        profile_key = self.profile_combo.currentData()
        profile = get_profile(profile_key)

        if profile is None:
            self.profile_info.setText("Custom profile")
            return

        self.frame_width_spin.setValue(profile.frame_width)
        self.frame_depth_spin.setValue(profile.frame_depth)
        self.mullion_spin.setValue(profile.mullion_width)
        self.glass_spin.setRange(profile.min_glass_thickness, profile.max_glass_thickness)
        self.glass_spin.setValue(profile.default_glass_thickness)

        if self.product_combo.currentData() == ProductKind.DOOR:
            self.threshold_spin.setValue(profile.threshold_height)
            if profile.default_panels >= 1 and self.panels_spin.minimum() <= profile.default_panels <= self.panels_spin.maximum():
                self.panels_spin.setValue(profile.default_panels)

        self.profile_info.setText(
            f"Glass {profile.min_glass_thickness:.0f}-{profile.max_glass_thickness:.0f} mm | "
            f"Depth {profile.frame_depth:.0f} mm | "
            f"Features H:{len(profile.horizontal_features)} V:{len(profile.vertical_features)}"
        )

    def get_parameters(self):
        from core.models import WindowModel

        return WindowModel(
            product_kind=self.product_combo.currentData(),
            window_type=self.type_combo.currentData(),
            profile_key=self.profile_combo.currentData(),
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            frame_width=self.frame_width_spin.value(),
            frame_depth=self.frame_depth_spin.value(),
            glass_thickness=self.glass_spin.value(),
            num_panels=self.panels_spin.value(),
            mullion_width=self.mullion_spin.value(),
            threshold_height=self.threshold_spin.value(),
        )

    def set_parameters(self, model):
        """Restore controls from a loaded WindowModel (without noisy emits)."""

        with self._suspend():
            product_idx = self.product_combo.findData(model.product_kind)
            if product_idx >= 0:
                self.product_combo.setCurrentIndex(product_idx)
            self._on_product_changed()

            type_idx = self.type_combo.findData(model.window_type)
            if type_idx >= 0:
                self.type_combo.setCurrentIndex(type_idx)
            self._on_type_changed()

            profile_idx = self.profile_combo.findData(model.profile_key)
            if profile_idx >= 0:
                self.profile_combo.setCurrentIndex(profile_idx)

            self.width_spin.setValue(model.width)
            self.height_spin.setValue(model.height)
            self.frame_width_spin.setValue(model.frame_width)
            self.frame_depth_spin.setValue(model.frame_depth)
            self.glass_spin.setValue(model.glass_thickness)
            self.panels_spin.setValue(model.num_panels)
            self.mullion_spin.setValue(model.mullion_width)
            self.threshold_spin.setValue(model.threshold_height)
