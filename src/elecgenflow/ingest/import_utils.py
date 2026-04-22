# src/elecgenflow/ingest/import_utils.py
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from .errors import ProjectLoadError


def import_module_from_path(module_name: str, file_path: Path) -> ModuleType:
    if not file_path.exists():
        raise ProjectLoadError(f"No existe el archivo: {file_path}")

    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ProjectLoadError(f"No se pudo crear spec para: {file_path}")

    module = importlib.util.module_from_spec(spec)
    try:
        # ✅ spec.loader ya es Loader aquí, cast innecesario
        spec.loader.exec_module(module)
    except Exception as exc:
        raise ProjectLoadError(f"Error importando {file_path}: {exc}") from exc

    return module


def call_if_exists(module: ModuleType, fn_name: str, *args: Any, **kwargs: Any) -> Any:
    fn = getattr(module, fn_name, None)
    if callable(fn):
        return fn(*args, **kwargs)
    return None
