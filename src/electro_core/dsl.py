# src/electro_core/dsl.py

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal


def parse_power(value: str | None) -> dict[str, Any]:
    """
    Parse simple de potencia. Devuelve un dict trazable:
      - si matchea: {"value": float, "unit": "kVA|VA|MVA|kW|W|MW|HP"}
      - si no matchea: {"raw": value}
    """
    if value is None:
        return {"value": 0.0, "unit": "kVA"}

    s = str(value).strip().replace(" ", "")
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(kW|kVA|W|VA|MW|MVA|HP)$", s, re.IGNORECASE)
    if not m:
        return {"raw": value}

    return {"value": float(m.group(1)), "unit": str(m.group(2))}


EndpointRole = Literal["entrypoint", "endpoint"]
EndpointKind = Literal["protection", "column", "terminal"]


@dataclass
class EndpointDecl:
    role: EndpointRole
    kind: EndpointKind
    tag: str
    prot_type: str | None = None
    source: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubCircuitIR:
    tag: str
    type: str
    phases: int | None
    load: dict[str, Any]
    protection: str
    desc: str = ""


@dataclass
class CircuitIR:
    tag: str
    type: str
    phases: int | None
    load: dict[str, Any]
    desc: str = ""
    protection: str = ""
    subcircuits: list[SubCircuitIR] = field(default_factory=list)


@dataclass
class BusIR:
    material: str
    coating: str
    capacity: int
    slots: int
    circuits: list[CircuitIR] = field(default_factory=list)
    reserves: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AuxiliaryIR:
    lighting: list[dict[str, Any]] = field(default_factory=list)
    service_socket: list[dict[str, Any]] = field(default_factory=list)
    climate_control: list[dict[str, Any]] = field(default_factory=list)
    door_indicators: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BoardIR:
    name: str
    system: str | None = None
    voltage: str | None = None
    freq: int | None = None
    grounding: str | None = None

    powered_by: dict[str, str] = field(default_factory=dict)
    ats: dict[str, Any] = field(default_factory=dict)
    main_protection: dict[str, Any] = field(default_factory=dict)
    leakage_protection: dict[str, Any] = field(default_factory=dict)
    metering: dict[str, Any] = field(default_factory=dict)

    buses: list[BusIR] = field(default_factory=list)
    auxiliary: AuxiliaryIR = field(default_factory=AuxiliaryIR)
    enclosure: dict[str, Any] = field(default_factory=dict)
    standards: list[str] = field(default_factory=list)

    endpoints: list[EndpointDecl] = field(default_factory=list)
    catalog: Any = None

    meta: dict[str, Any] = field(default_factory=dict)


class Board:
    ENTRYPOINT_MAIN_PROT_TAG = "IG"

    def __init__(self, name: str) -> None:
        self._ir = BoardIR(name=name)

    @staticmethod
    def create(name: str) -> Board:
        return Board(name)

    # ✅ alias: Board.id("TS-CRITICOS")
    @staticmethod
    def id(name: str) -> Board:
        return Board.create(name)

    def configured_as(
        self,
        system: str | None = None,
        *,
        phases: int | None = None,
        voltage: str,
        freq: int,
        grounding_system: str | None = None,
    ) -> Board:
        """
        Compat + nuevo formato:
          - viejo: configured_as("TRIFASICO", voltage="380/220V", freq=50)
          - nuevo: configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        """
        if system is not None:
            self._ir.system = system

        if phases is not None:
            p = int(phases)
            self._ir.meta["phases"] = p
            self._ir.system = "TRIFASICO" if p == 3 else "MONOFASICO"

        self._ir.voltage = voltage
        self._ir.freq = int(freq)

        if grounding_system is not None:
            self._ir.grounding = grounding_system

        return self

    def grounding_system(self, grounding: str) -> Board:
        self._ir.grounding = grounding
        return self

    def powered_by(self, *, main: str, backup: str) -> Board:
        self._ir.powered_by = {"main": main, "backup": backup}
        return self

    def equipped_with_ats(self, *, poles: int, amps: int, type: str) -> Board:  # noqa: A002
        self._ir.ats = {"poles": poles, "amps": amps, "type": type}
        return self

    def main_protection(self, prot: Any) -> Board:
        if isinstance(prot, dict):
            self._ir.main_protection = prot
            kind = str(prot.get("kind", "PROT"))
        else:
            self._ir.main_protection = {
                "kind": prot.__class__.__name__,
                **getattr(prot, "__dict__", {}),
            }
            kind = prot.__class__.__name__

        self._register_endpoint(
            role="entrypoint",
            kind="protection",
            tag=self.ENTRYPOINT_MAIN_PROT_TAG,
            prot_type=kind,
            source="main_protection",
        )
        return self

    def leakage_protection(self, prot: Any) -> Board:
        if isinstance(prot, dict):
            self._ir.leakage_protection = prot
        else:
            self._ir.leakage_protection = {
                "kind": prot.__class__.__name__,
                **getattr(prot, "__dict__", {}),
            }
        return self

    def metering_via(self, protocol: str, *, features: list[str]) -> Board:
        self._ir.metering = {"protocol": protocol, "features": features}
        return self

    def distribution_bus(
        self, *, material: str, coating: str, capacity: int, slots: int
    ) -> BusBuilder:
        bus = BusIR(material=material, coating=coating, capacity=capacity, slots=slots)
        self._ir.buses.append(bus)
        return BusBuilder(self, bus)

    def auxiliary_circuits(self) -> AuxiliaryBuilder:
        return AuxiliaryBuilder(self)

    def enclosure(self, **kwargs: Any) -> Board:
        self._ir.enclosure = dict(kwargs)
        return self

    def complying_with(self, standards: list[str]) -> Board:
        self._ir.standards = list(standards)
        return self

    def build(self, catalog: Any = None) -> dict[str, Any]:
        self._ir.catalog = catalog
        return asdict(self._ir)

    def _register_endpoint(
        self,
        *,
        role: EndpointRole,
        kind: EndpointKind,
        tag: str,
        prot_type: str | None = None,
        source: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        for e in self._ir.endpoints:
            if e.role == role and e.kind == kind and e.tag == tag:
                return
        self._ir.endpoints.append(
            EndpointDecl(
                role=role,
                kind=kind,
                tag=tag,
                prot_type=prot_type,
                source=source,
                meta=meta or {},
            )
        )


class BusBuilder:
    def __init__(self, board: Board, bus: BusIR) -> None:
        self._board = board
        self._bus = bus

    def add_circuit(
        self,
        *,
        tag: str,
        type: str,  # noqa: A002
        load: str | None = None,
        desc: str = "",
        protection: str = "",
        phases: int | None = None,
    ) -> BusBuilder | CircuitGroupBuilder:
        c = CircuitIR(
            tag=tag,
            type=type,
            phases=phases,
            load=parse_power(load),
            desc=desc,
            protection=protection,
        )
        self._bus.circuits.append(c)

        if protection:
            self._board._register_endpoint(
                role="endpoint",
                kind="protection",
                tag=str(tag),
                prot_type=str(protection),
                source="circuit",
                meta={
                    "circuit_type": type,
                    "phases": str(phases) if phases is not None else "",
                },
            )

        if type.lower() in ("hvac", "group", "panel", "parent"):
            return CircuitGroupBuilder(parent_bus=self, parent_circuit=c)

        return self

    def equipped_reserve(self, *, device: str, qty: int) -> Board:
        self._bus.reserves.append({"device": device, "qty": qty})
        return self._board

    def __getattr__(self, name: str) -> Any:
        return getattr(self._board, name)


class CircuitGroupBuilder:
    def __init__(self, parent_bus: BusBuilder, parent_circuit: CircuitIR) -> None:
        self._parent_bus = parent_bus
        self._circuit = parent_circuit

    def add_sub_circuit(
        self,
        *,
        tag: str,
        load: str | None = None,
        protection: str,
        desc: str = "",
        type: str | None = None,  # noqa: A002
        phases: int | None = None,
    ) -> CircuitGroupBuilder:
        sc_type = type if type is not None else self._circuit.type
        sc = SubCircuitIR(
            tag=tag,
            type=sc_type,
            phases=phases,
            load=parse_power(load),
            protection=protection,
            desc=desc,
        )
        self._circuit.subcircuits.append(sc)

        parent_tag = str(self._circuit.tag)
        full_tag = f"{parent_tag}:{tag}"

        if protection:
            self._parent_bus._board._register_endpoint(
                role="endpoint",
                kind="protection",
                tag=full_tag,
                prot_type=str(protection),
                source="subcircuit",
                meta={
                    "parent": parent_tag,
                    "type": sc_type,
                    "phases": str(phases) if phases is not None else "",
                },
            )

        return self

    def __getattr__(self, name: str) -> Any:
        return getattr(self._parent_bus, name)


class AuxiliaryBuilder:
    def __init__(self, board: Board) -> None:
        self._board = board

    def lighting(self, **kwargs: Any) -> AuxiliaryBuilder:
        self._board._ir.auxiliary.lighting.append(dict(kwargs))
        return self

    def service_socket(self, **kwargs: Any) -> AuxiliaryBuilder:
        self._board._ir.auxiliary.service_socket.append(dict(kwargs))
        return self

    def climate_control(self, **kwargs: Any) -> AuxiliaryBuilder:
        self._board._ir.auxiliary.climate_control.append(dict(kwargs))
        return self

    def door_indicators(self, **kwargs: Any) -> AuxiliaryBuilder:
        self._board._ir.auxiliary.door_indicators.append(dict(kwargs))
        return self

    def __getattr__(self, name: str) -> Any:
        return getattr(self._board, name)


class MCCB:
    def __init__(self, *, poles: int, amps: int, kA: int) -> None:  # noqa: N803
        self.poles = poles
        self.amps = amps
        self.kA = kA


class RCCB:
    def __init__(
        self,
        *,
        type: str,  # noqa: A002
        sensitivity_mA: int | None = None,  # noqa: N803
        sensitivity: str | None = None,
        selective: bool = False,
    ) -> None:
        self.type = type
        # compat: permitir sensitivity="300mA" o sensitivity_mA=300
        if sensitivity is None and sensitivity_mA is not None:
            self.sensitivity = f"{int(sensitivity_mA)}mA"
        else:
            self.sensitivity = sensitivity or ""
        self.selective = selective
