# src/electro_core/network.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


# -----------------------------
# Compatibility: Registry
# -----------------------------
@dataclass
class Registry:
    """
    Placeholder de compatibilidad.
    Algunos módulos legacy importan Registry desde electro_core.network.
    La implementación real del Registry vive en elecgenflow (ingest/registry_bootstrap).
    """

    meta: dict[str, Any] = field(default_factory=dict)


# -----------------------------
# Models
# -----------------------------
@dataclass(frozen=True)
class Endpoint:
    board: str
    column: str | None = None
    protection: str | None = None
    terminal: str | None = None
    load: str | None = None


Conductor = Literal["CU", "AL"]
Insulation = Literal["PVC", "XLPE"]
InstallMethod = str  # "A1", "B2", "C", "E", "D1", "D2", "F", "G", etc.
CableKind = Literal["unipolar", "multipolar"]
UnipolarOrientation = Literal["horizontal", "vertical"]


@dataclass
class WireConfig:
    kind: CableKind | None = None
    unipolar_orientation: UnipolarOrientation | None = None

    conductor: Conductor | None = None
    insulation: Insulation | None = None
    install_method: InstallMethod | None = None

    # multipolar option: PE included in the same cable
    protection_cable_included: bool | None = None

    # buried conditions (optional for D1/D2, etc.)
    buried_depth_m: float | None = None

    # meta: aquí guardamos agrupamiento / paralelos / arrangement / etc.
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "unipolar_orientation": self.unipolar_orientation,
            "conductor": self.conductor,
            "insulation": self.insulation,
            "install_method": self.install_method,
            "protection_cable_included": self.protection_cable_included,
            "buried_depth_m": self.buried_depth_m,
            "meta": dict(self.meta),
        }


@dataclass
class NetworkLink:
    origin: Endpoint
    destination: Endpoint

    # Preferred stable id
    wire_id: str | None = None

    # Backward compatible tags
    wire_tag: str | None = None
    wire: str | None = None

    wire_config: WireConfig = field(default_factory=WireConfig)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "origin": {
                "board": self.origin.board,
                "column": self.origin.column,
                "protection": self.origin.protection,
                "terminal": self.origin.terminal,
            },
            "destination": {
                "board": self.destination.board,
                "column": self.destination.column,
                "protection": self.destination.protection,
                "terminal": self.destination.terminal,
                "load": self.destination.load,
            },
            # wire legacy: el pipeline actual usa lk["wire"] como identificador visible
            "wire": self.wire or self.wire_tag or self.wire_id or "",
            "wire_id": self.wire_id,
            "wire_config": self.wire_config.to_dict(),
            "meta": self.meta,
        }


# -----------------------------
# DSL / Builders
# -----------------------------
class Network:
    def __init__(self) -> None:
        self.links: list[NetworkLink] = []

    def supply_from(self, board: str) -> LinkBuilder:
        origin = Endpoint(board=board)
        return LinkBuilder(self, origin=origin, dest=Endpoint(board=""))

    def from_source(self, board: str) -> LinkBuilder:
        return self.supply_from(board)


class LinkBuilder:
    def __init__(self, net: Network, *, origin: Endpoint, dest: Endpoint) -> None:
        self._net = net
        self._origin = origin
        self._dest = dest

        self._wire_id: str | None = None
        self._wire_tag: str | None = None
        self._wire: str | None = None  # legacy string "wire"

        self._wire_cfg: WireConfig = WireConfig()
        self._meta: dict[str, Any] = {}

    # ---- origin / dest selectors
    def column(self, tag: str) -> LinkBuilder:
        if not self._dest.board:
            self._origin = Endpoint(
                board=self._origin.board,
                column=tag,
                protection=self._origin.protection,
                terminal=self._origin.terminal,
                load=self._origin.load,
            )
        else:
            self._dest = Endpoint(
                board=self._dest.board,
                column=tag,
                protection=self._dest.protection,
                terminal=self._dest.terminal,
                load=self._dest.load,
            )
        return self

    def protection(self, tag: str) -> LinkBuilder:
        if not self._dest.board:
            self._origin = Endpoint(
                board=self._origin.board,
                column=self._origin.column,
                protection=tag,
                terminal=self._origin.terminal,
                load=self._origin.load,
            )
        else:
            self._dest = Endpoint(
                board=self._dest.board,
                column=self._dest.column,
                protection=tag,
                terminal=self._dest.terminal,
                load=self._dest.load,
            )
        return self

    def terminal(self, tag: str) -> LinkBuilder:
        if not self._dest.board:
            self._origin = Endpoint(
                board=self._origin.board,
                column=self._origin.column,
                protection=self._origin.protection,
                terminal=tag,
                load=self._origin.load,
            )
        else:
            self._dest = Endpoint(
                board=self._dest.board,
                column=self._dest.column,
                protection=self._dest.protection,
                terminal=tag,
                load=self._dest.load,
            )
        return self

    def to(self, board: str) -> LinkBuilder:
        self._dest = Endpoint(board=board)
        return self

    def ends_at_load(self, load_tag: str) -> LinkBuilder:
        self._dest = Endpoint(board=self._dest.board or "", load=load_tag)
        return self

    # ---- wire identification
    def with_wire_id(self, wire_id: str) -> LinkBuilder:
        self._wire_id = wire_id
        return self

    def with_wire(self, wire_tag: str) -> LinkBuilder:
        self._wire_tag = wire_tag
        return self

    # legacy
    def with_wire_legacy(self, wire: str) -> LinkBuilder:
        self._wire = wire
        return self

    def meta(self, **kwargs: Any) -> LinkBuilder:
        self._meta.update(kwargs)
        return self

    # configured_as DOES NOT close; WireConfigBuilder.done closes everything
    def configured_as(self) -> WireConfigBuilder:
        return WireConfigBuilder(self)

    # finalize link
    def done(self) -> Network:
        link = NetworkLink(
            origin=self._origin,
            destination=self._dest,
            wire_id=self._wire_id,
            wire_tag=self._wire_tag,
            wire=self._wire,
            wire_config=self._wire_cfg,
            meta=self._meta,
        )
        self._net.links.append(link)
        return self._net


class WireConfigBuilder:
    """
    Config builder.
    IMPORTANT: .done() closes config + link and returns Network (one done only).
    """

    def __init__(self, parent: LinkBuilder) -> None:
        self._p = parent

    def multipolar(self) -> WireConfigBuilder:
        self._p._wire_cfg.kind = "multipolar"
        return self

    def unipolar(self, orientation: UnipolarOrientation) -> WireConfigBuilder:
        self._p._wire_cfg.kind = "unipolar"
        self._p._wire_cfg.unipolar_orientation = orientation
        return self

    def with_protection_cable_included(self) -> WireConfigBuilder:
        self._p._wire_cfg.protection_cable_included = True
        return self

    def without_protection_cable_included(self) -> WireConfigBuilder:
        self._p._wire_cfg.protection_cable_included = False
        return self

    def with_insulation(self, insulation: Insulation) -> WireConfigBuilder:
        self._p._wire_cfg.insulation = insulation
        return self

    def with_conductor(self, conductor: Conductor) -> WireConfigBuilder:
        self._p._wire_cfg.conductor = conductor
        return self

    # ✅ aliases “cómodos” (como tu ejemplo Ford)
    def insulation(self, insulation: Insulation) -> WireConfigBuilder:
        return self.with_insulation(insulation)

    def conductor(self, conductor: Conductor) -> WireConfigBuilder:
        return self.with_conductor(conductor)

    def installed_in(self, method: InstallMethod) -> WireConfigBuilder:
        self._p._wire_cfg.install_method = method
        return self

    def buried_at(self, *, depth_m: float) -> WireConfigBuilder:
        self._p._wire_cfg.buried_depth_m = float(depth_m)
        return self

    def circuits(self, *, parallel: int = 1, grouped: int = 1) -> WireConfigBuilder:
        """
        parallel: cantidad de ternas/cables en paralelo para ESTE MISMO feeder.
        grouped: cantidad de circuitos cargados en una misma canalización.
        """
        p = int(parallel) if int(parallel) >= 1 else 1
        g = int(grouped) if int(grouped) >= 1 else 1
        self._p._wire_cfg.meta["parallel"] = p
        self._p._wire_cfg.meta["grouped"] = g
        return self

    def meta(self, **kwargs: Any) -> WireConfigBuilder:
        self._p._wire_cfg.meta.update(kwargs)
        return self

    def done(self) -> Network:
        return self._p.done()
