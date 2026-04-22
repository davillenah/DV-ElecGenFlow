"""
electro_core — SDK/DSL público del motor ElecGenFlow.

IMPORTANTE:
- Este paquete vive dentro del repo del MOTOR.
- El usuario (Project/Plant/...) SOLO lo consume.
- El usuario NO escribe electro_core.
"""

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
