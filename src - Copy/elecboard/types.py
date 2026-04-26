from __future__ import annotations

from enum import Enum


class Phase(str, Enum):
    """Electrical phase identifiers for logical modelling.

    Note: This is a logical representation. No magnitudes are implied.
    """

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    N = "N"
    PE = "PE"


class TopologyKind(str, Enum):
    """Topology intent declared for the logical network."""

    UNKNOWN = "unknown"
    RADIAL = "radial"
    MESHED = "meshed"


class BoardLevel(str, Enum):
    """Logical board voltage level (no magnitudes)."""

    MV = "MV"
    LV = "LV"


class NodeKind(str, Enum):
    BUS = "bus"
    JUNCTION = "junction"
    TERMINAL = "terminal"


class BranchKind(str, Enum):
    FEEDER = "feeder"
    TIE = "tie"
    INTERNAL = "internal"


class LoadKind(str, Enum):
    GENERIC = "generic"
    LIGHTING = "lighting"
    MOTOR = "motor"
    HVAC = "hvac"


class SourceKind(str, Enum):
    UTILITY = "utility"
    GENERATOR = "generator"
    TRANSFORMER = "transformer"
