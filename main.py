"""
Fenestration Designer – Entry Point
====================================
Parametric window & door designer with cross-section views.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from ui.main_window import MainWindow


# ═══════════════════════════════════════════════════════════════════════
#  Dark Theme Stylesheet
# ═══════════════════════════════════════════════════════════════════════

DARK_THEME = """

/* ── Global ─────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Toolbar ────────────────────────────────────────────────────── */
#Toolbar {
    background-color: #161822;
    border-bottom: 1px solid #252840;
}

/* ── Input Panel ────────────────────────────────────────────────── */
#InputPanel, #InputPanel QScrollArea, #InputPanel QScrollArea > QWidget {
    background-color: #13141f;
    border-right: 1px solid #252840;
}

/* ── Buttons ────────────────────────────────────────────────────── */
QPushButton {
    background-color: #1c1e30;
    border: 1px solid #2d3148;
    border-radius: 6px;
    padding: 6px 14px;
    color: #94a3b8;
    font-weight: 500;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #252840;
    border-color: #4f5a82;
    color: #e2e8f0;
}
QPushButton:pressed {
    background-color: #2d3148;
}
QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #4338ca, stop:1 #3730a3);
    border-color: #6366f1;
    color: #ffffff;
    font-weight: 600;
}

/* ── Spin Boxes ─────────────────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {
    background-color: #1c1e30;
    border: 1px solid #2d3148;
    border-radius: 6px;
    padding: 5px 8px;
    color: #e2e8f0;
    min-height: 26px;
    selection-background-color: #4338ca;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #6366f1;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #2d3148;
    border-bottom: 1px solid #2d3148;
    border-top-right-radius: 6px;
    background-color: #252840;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    border-left: 1px solid #2d3148;
    border-bottom-right-radius: 6px;
    background-color: #252840;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 8px; height: 8px;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 8px; height: 8px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #3730a3;
}

/* ── Combo Box ──────────────────────────────────────────────────── */
QComboBox {
    background-color: #1c1e30;
    border: 1px solid #2d3148;
    border-radius: 6px;
    padding: 5px 10px;
    color: #e2e8f0;
    min-height: 26px;
}
QComboBox:focus { border-color: #6366f1; }
QComboBox::drop-down {
    border-left: 1px solid #2d3148;
    width: 24px;
    background-color: #252840;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1c1e30;
    border: 1px solid #2d3148;
    color: #e2e8f0;
    selection-background-color: #4338ca;
    selection-color: #ffffff;
    padding: 4px;
}

/* ── Group Box ──────────────────────────────────────────────────── */
QGroupBox {
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #252840;
    border-radius: 10px;
    margin-top: 18px;
    padding: 22px 14px 14px 14px;
    color: #8892b0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #a78bfa;
    font-weight: 700;
}

/* ── Labels ─────────────────────────────────────────────────────── */
QLabel {
    color: #8892b0;
    font-size: 12px;
}

/* ── Splitter ───────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #252840;
    width: 2px;
}
QSplitter::handle:hover {
    background-color: #6366f1;
}

/* ── Status Bar ─────────────────────────────────────────────────── */
QStatusBar {
    background-color: #161822;
    border-top: 1px solid #252840;
    color: #64748b;
    font-size: 12px;
    padding: 2px 12px;
    min-height: 24px;
}

/* ── Scroll Bars ────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0f1117;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2d3148;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #4f5a82; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #0f1117;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2d3148;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #4f5a82; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Graphics View ──────────────────────────────────────────────── */
QGraphicsView {
    border: none;
}

/* ── Tooltips ───────────────────────────────────────────────────── */
QToolTip {
    background-color: #1c1e30;
    border: 1px solid #4f5a82;
    color: #e2e8f0;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}
"""


def main():
    # ── OpenGL surface format (must be set before QApplication) ────
    from PySide6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat()
    fmt.setVersion(2, 1)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    fmt.setDepthBufferSize(24)
    fmt.setSamples(4)  # 4× MSAA
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)

    # Global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Apply dark theme
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
