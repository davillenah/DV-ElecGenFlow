"""Elecboard IR (EPIC-3)

Logical Intermediate Representation (IR) for electrical systems.

This package defines:
- Pydantic models for the logical network (boards, nodes, branches, loads, sources)
- Structural validation (connectivity, phase compatibility, topology constraints)
- JSON serialisation/deserialisation helpers
"""

from .ir import ElecboardIR
from .types import (
    BoardLevel,
    BranchKind,
    LoadKind,
    NodeKind,
    Phase,
    SourceKind,
    TopologyKind,
)

__all__ = [
    "BoardLevel",
    "BranchKind",
    "ElecboardIR",
    "LoadKind",
    "NodeKind",
    "Phase",
    "SourceKind",
    "TopologyKind",
]
