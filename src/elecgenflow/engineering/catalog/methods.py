# src/elecgenflow/engineering/catalog/methods.py

from enum import Enum


class InstallationRefMethod(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C = "C"
    D1 = "D1"
    D2 = "D2"
    E = "E"
    F = "F"
    G = "G"


class CableForm(str, Enum):
    UNIPOLAR = "UNIPOLAR"
    MULTIPOLAR = "MULTIPOLAR"


class PhaseSystem(str, Enum):
    SINGLE_PHASE = "MONO"
    THREE_PHASE = "TRI"
