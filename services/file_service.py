"""
File service – save / load WindowModel designs as JSON.
"""

from __future__ import annotations

import json
from typing import Optional

from core.models import WindowModel


class FileService:
    """Handles persisting and restoring window designs."""

    @staticmethod
    def save(model: WindowModel, filepath: str) -> None:
        """Serialise *model* to a JSON file at *filepath*."""
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(model.to_dict(), fh, indent=2, ensure_ascii=False)

    @staticmethod
    def load(filepath: str) -> Optional[WindowModel]:
        """Deserialise a JSON file into a WindowModel.

        Returns ``None`` if the file cannot be read or parsed.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return WindowModel.from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            print(f"[FileService] Failed to load '{filepath}': {exc}")
            return None
