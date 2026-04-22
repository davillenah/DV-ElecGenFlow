# src/elecgenflow/ingest/errors.py
from __future__ import annotations


class ProjectLoadError(RuntimeError):
    pass


class MissingTagError(ValueError):
    """Error inmediato cuando un tag referenciado no existe en Registry auto-generado."""


class InvalidLinkError(ValueError):
    """Error cuando un vínculo no define ningún selector (column/protection/terminal)."""
