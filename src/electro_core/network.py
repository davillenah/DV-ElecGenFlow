from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class Registry:
    """
    Placeholder Registry (DB/JSON in future).
    En EPIC-04.00 NO bloquea el DSL runtime.
    """

    def __init__(self, strict: bool = True) -> None:
        self.strict: bool = strict
        self.boards: set[str] = set()
        self.columns: set[tuple[str, str]] = set()
        self.protections: set[tuple[str, str]] = set()
        self.terminals: set[tuple[str, str]] = set()
        self.wires: set[str] = set()


@dataclass(frozen=True)
class EndpointRef:
    board: str | None = None
    column: str | None = None
    protection: str | None = None
    terminal: str | None = None
    load: str | None = None  # destino final (carga virtual)


@dataclass(frozen=True)
class SupplyLinkRef:
    origin: EndpointRef
    destination: EndpointRef
    wire: str
    meta: dict[str, Any] = field(default_factory=dict)


class _EndpointBuilder:
    def __init__(self, parent: _SupplyBuilder, *, is_origin: bool) -> None:
        self._parent = parent
        self._is_origin = is_origin

    def column(self, tag: str) -> _EndpointBuilder:
        if self._is_origin:
            self._parent._origin_col = tag
        else:
            self._parent._dest_col = tag
        return self

    def protection(self, tag: str) -> _EndpointBuilder:
        if self._is_origin:
            self._parent._origin_prot = tag
        else:
            self._parent._dest_prot = tag
        return self

    def terminal(self, tag: str) -> _EndpointBuilder:
        if self._is_origin:
            self._parent._origin_term = tag
        else:
            self._parent._dest_term = tag
        return self

    # permite saltar a .to(...) sin cerrar
    def to(self, board: str) -> _EndpointBuilder:
        return self._parent.to(board)

    # ✅ proxy para permitir chain: .to(...).protection(...).with_wire(...).done()
    def with_wire(self, wire: str) -> _SupplyBuilder:
        return self._parent.with_wire(wire)

    def meta(self, **meta: Any) -> _SupplyBuilder:
        return self._parent.meta(**meta)

    def done(self) -> Network:
        return self._parent.done()

    def ends_at_load(self, load_tag: str) -> Network:
        return self._parent.ends_at_load(load_tag)


class _SupplyBuilder:
    def __init__(self, network: Network, origin_board: str) -> None:
        self._net = network
        self._origin_board = origin_board

        self._origin_col: str | None = None
        self._origin_prot: str | None = None
        self._origin_term: str | None = None

        self._dest_board: str | None = None
        self._dest_col: str | None = None
        self._dest_prot: str | None = None
        self._dest_term: str | None = None

        self._dest_load: str | None = None

        self._wire: str | None = None
        self._meta: dict[str, Any] = {}

    # origen
    def column(self, tag: str) -> _SupplyBuilder:
        self._origin_col = tag
        return self

    def protection(self, tag: str) -> _SupplyBuilder:
        self._origin_prot = tag
        return self

    def terminal(self, tag: str) -> _SupplyBuilder:
        self._origin_term = tag
        return self

    # destino board
    def to(self, board: str) -> _EndpointBuilder:
        self._dest_board = board
        self._dest_load = None
        return _EndpointBuilder(self, is_origin=False)

    # wire + meta
    def with_wire(self, wire: str) -> _SupplyBuilder:
        self._wire = wire
        return self

    def meta(self, **meta: Any) -> _SupplyBuilder:
        self._meta.update(meta)
        return self

    # finalizar (destino board)
    def done(self) -> Network:
        if self._wire is None:
            raise ValueError("Falta .with_wire(<WIRE_ID>)")
        if self._dest_board is None:
            raise ValueError("Falta .to(<BOARD_DESTINO>)")

        if self._origin_col is None and self._origin_prot is None and self._origin_term is None:
            raise ValueError(
                "Origen inválido: debe definir .column(...) y/o .protection(...) y/o .terminal(...)"
            )

        if self._dest_col is None and self._dest_prot is None and self._dest_term is None:
            raise ValueError(
                "Destino inválido: debe definir .column(...) y/o .protection(...) y/o .terminal(...)"
            )

        origin = EndpointRef(
            board=self._origin_board,
            column=self._origin_col,
            protection=self._origin_prot,
            terminal=self._origin_term,
        )
        dest = EndpointRef(
            board=self._dest_board,
            column=self._dest_col,
            protection=self._dest_prot,
            terminal=self._dest_term,
        )

        self._net.links.append(
            SupplyLinkRef(origin=origin, destination=dest, wire=self._wire, meta=dict(self._meta))
        )
        return self._net

    # finalizar (destino carga final)
    def ends_at_load(self, load_tag: str) -> Network:
        if self._wire is None:
            raise ValueError("Falta .with_wire(<WIRE_ID>)")
        if not isinstance(load_tag, str) or not load_tag:
            raise ValueError("Falta load_tag válido en .ends_at_load(<LOAD_TAG>)")

        if self._origin_col is None and self._origin_prot is None and self._origin_term is None:
            raise ValueError(
                "Origen inválido: debe definir .column(...) y/o .protection(...) y/o .terminal(...)"
            )

        origin = EndpointRef(
            board=self._origin_board,
            column=self._origin_col,
            protection=self._origin_prot,
            terminal=self._origin_term,
        )
        dest = EndpointRef(load=load_tag)

        meta = dict(self._meta)
        meta["ends_at_load"] = True

        self._net.links.append(
            SupplyLinkRef(origin=origin, destination=dest, wire=self._wire, meta=meta)
        )
        return self._net


class Network:
    def __init__(self, registry: Registry | None = None) -> None:
        self.registry = registry
        self.links: list[SupplyLinkRef] = []

    def supply_from(self, board: str) -> _SupplyBuilder:
        return _SupplyBuilder(self, board)

    def from_source(self, board: str) -> _SupplyBuilder:
        return self.supply_from(board)
