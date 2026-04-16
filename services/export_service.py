"""
Export service for PNG and PDF outputs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QPageLayout, QPageSize, QColor, QFont

from config.settings import EXPORT

if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsView
    from core.models import WindowModel


class ExportService:
    """High-resolution export for PNG and PDF formats."""

    @staticmethod
    def export_png(
        canvas: "QGraphicsView",
        filepath: str,
        width: int = EXPORT["png_width"],
        height: int = EXPORT["png_height"],
    ) -> None:
        scene = canvas.scene()
        rect = scene.itemsBoundingRect()
        margin = 60
        rect.adjust(-margin, -margin, margin, margin)

        image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        image.fill(QColor("#FFFFFF"))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter, QRectF(0, 0, width, height), rect)
        painter.end()
        image.save(filepath)

    @staticmethod
    def export_pdf(
        canvas: "QGraphicsView",
        filepath: str,
        model: Optional["WindowModel"] = None,
    ) -> None:
        from PySide6.QtPrintSupport import QPrinter

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scene = canvas.scene()
        source_rect = scene.itemsBoundingRect()
        margin = 60
        source_rect.adjust(-margin, -margin, margin, margin)

        page_rect = QRectF(printer.pageRect(QPrinter.Unit.DevicePixel))

        if model is not None:
            title_h = page_rect.height() * 0.08
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            painter.drawText(
                QRectF(page_rect.x(), page_rect.y(), page_rect.width(), title_h),
                Qt.AlignmentFlag.AlignCenter,
                (
                    f"Fenestration Designer - {model.product_kind.value.title()} / "
                    f"{model.window_type.value.replace('_', ' ').title()} - "
                    f"{model.width:.0f} x {model.height:.0f} mm"
                ),
            )
            page_rect.setTop(page_rect.top() + title_h)

        scene.render(painter, page_rect, source_rect)
        painter.end()
