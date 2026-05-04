# src/elecgenflow/engineering/sizing/sizing_case.py

from __future__ import annotations

from dataclasses import dataclass, field

from elecgenflow.engineering.catalog.methods import CableForm, InstallationRefMethod, PhaseSystem


@dataclass(frozen=True)
class ElectricalContext:
    """
    Contexto eléctrico mínimo para dimensionamiento.

    - phase_system: MONO/TRI
    - voltage_v:
        - si TRI: usar V_LL (ej 380)
        - si MONO: usar V_LN (ej 220)
    - power_factor:
        - opcional (si la carga viene en kW y necesitás pasar a kVA)
    """

    phase_system: PhaseSystem
    voltage_v: float
    frequency_hz: float = 50.0
    power_factor: float | None = None


def _default_ctx() -> ElectricalContext:
    """
    Default factory para evitar RUF009: no ejecutar llamadas en defaults de dataclass.
    (La creación del objeto debe ocurrir por instancia, no una única vez al definir la clase.)
    [1](https://professional-electrician.com/technical/requirements-protection-overload/)
    """
    return ElectricalContext(
        phase_system=PhaseSystem.THREE_PHASE,
        voltage_v=380.0,
        frequency_hz=50.0,
        power_factor=None,
    )


@dataclass(frozen=True)
class SizingCase:
    """
    Caso mínimo para dimensionamiento.

    Nota: este dataclass NO calcula nada por sí mismo;
    solo transporta entradas normalizadas hacia el motor.
    """

    origin_board: str
    dest_board: str
    circuit_tag: str
    wire_id: str

    # carga (preferible kVA)
    load_kva: float | None = None
    load_kw: float | None = None

    # wire config
    method: InstallationRefMethod = InstallationRefMethod.E
    cable_form: CableForm = CableForm.MULTIPOLAR
    insulation: str = "PVC"
    conductor: str = "AL"

    # condiciones (más adelante: longitud real desde link)
    length_m: float = 1.0
    ambient_air_c: float = 40.0
    grouped_circuits: int = 1
    soil_resistivity: float | None = None
    burial_depth_m: float | None = None

    # contexto eléctrico (✅ default_factory para cumplir RUF009)
    ctx: ElectricalContext = field(default_factory=_default_ctx)
