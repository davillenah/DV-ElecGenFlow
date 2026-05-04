# src/electro_core/__init__.py
from __future__ import annotations

from importlib import import_module
from typing import Any

from .board_assembly import CCM, TGBT, CatalogConfig
from .compute import board_local_load_kw, cable_context, total_board_load_kw
from .dsl import MCCB, RCCB, Board
from .network import Network, Registry

__all__ = [
    "CCM",
    "MCCB",
    "RCCB",
    "TGBT",
    "Board",
    "CatalogConfig",
    "Network",
    "Registry",
    "board_local_load_kw",
    "cable_context",
    "total_board_load_kw",
]


def __getattr__(name: str) -> Any:
    """
    Compatibilidad: permite `from electro_core import Board, MCCB, RCCB, TGBT, ...`
    aunque __init__.py no los importe explícitamente.

    Busca el símbolo en submódulos típicos de electro_core y lo cachea en globals().
    """
    candidates = [
        "electro_core",
        "electro_core.board",
        "electro_core.boards",
        "electro_core.components",
        "electro_core.devices",
        "electro_core.switchgear",
        "electro_core.tgbt",
        "electro_core.assembly",
        "electro_core.models",
    ]

    for mod_name in candidates:
        try:
            mod = import_module(mod_name)
        except Exception:
            continue
        if hasattr(mod, name):
            val = getattr(mod, name)
            globals()[name] = val  # cache
            return val

    raise AttributeError(f"module 'electro_core' has no attribute {name!r}")
