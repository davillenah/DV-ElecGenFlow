from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# -----------------------------
# Registry: TODO vive en DB/JSON
# (acá solo validamos existencia)
# -----------------------------
class Registry:
    def __init__(self, strict: bool = True) -> None:
        self.strict: bool = strict
        self.boards: set[str] = set()
        self.columns: set[tuple[str, str]] = set()  # (board, column)
        self.protections: set[tuple[str, str]] = set()  # (board, protection)
        self.terminals: set[tuple[str, str]] = set()  # (board, terminal)
        self.wires: set[str] = set()

    def _req(self, cond: bool, msg: str) -> None:
        if not cond and self.strict:
            raise KeyError(msg)

    def require_board(self, board: str) -> None:
        self._req(board in self.boards, f"Board inexistente: {board}")
        if not self.strict:
            self.boards.add(board)

    def require_column(self, board: str, col: str) -> None:
        self.require_board(board)
        self._req((board, col) in self.columns, f"Columna inexistente: {board}:{col}")
        if not self.strict:
            self.columns.add((board, col))

    def require_protection(self, board: str, prot: str) -> None:
        self.require_board(board)
        self._req((board, prot) in self.protections, f"Protección inexistente: {board}:{prot}")
        if not self.strict:
            self.protections.add((board, prot))

    def require_terminal(self, board: str, term: str) -> None:
        self.require_board(board)
        self._req((board, term) in self.terminals, f"Bornera inexistente: {board}:{term}")
        if not self.strict:
            self.terminals.add((board, term))

    def require_wire(self, wire: str) -> None:
        self._req(wire in self.wires, f"Wire inexistente: {wire}")
        if not self.strict:
            self.wires.add(wire)


# -----------------------------
# IR mínimo basado en referencias (solo tags)
# -----------------------------
@dataclass(frozen=True)
class EndpointRef:
    board: str
    column: str | None = None
    protection: str | None = None
    terminal: str | None = None  # bornera


@dataclass(frozen=True)
class SupplyLinkRef:
    origin: EndpointRef
    destination: EndpointRef
    wire: str
    meta: dict[str, Any] = field(default_factory=dict)


# -----------------------------
# Fluent Builders
# -----------------------------
class _EndpointBuilder:
    """
    Builder reusable para setear atributos de origen/destino sin ambigüedad:
      .column(...)
      .protection(...)
      .terminal(...)
    """

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

    def to(self, board: str) -> _EndpointBuilder:
        return self._parent.to(board)


class _SupplyBuilder:
    """
    Crea 1 vínculo supply link:
    network.supply_from("TGBT").column("DOS").protection("Q59").terminal("X48:1")
           .to("TS").terminal("X23:6").with_wire("W123").done()
    """

    def __init__(self, network: Network, origin_board: str) -> None:
        self._net = network
        self._reg = network.registry

        self._origin_board: str = origin_board
        self._dest_board: str | None = None

        self._origin_col: str | None = None
        self._origin_prot: str | None = None
        self._origin_term: str | None = None

        self._dest_col: str | None = None
        self._dest_prot: str | None = None
        self._dest_term: str | None = None

        self._wire: str | None = None
        self._meta: dict[str, Any] = {}

        # validar board origen
        self._reg.require_board(origin_board)

    def column(self, tag: str) -> _SupplyBuilder:
        self._origin_col = tag
        return self

    def protection(self, tag: str) -> _SupplyBuilder:
        self._origin_prot = tag
        return self

    def terminal(self, tag: str) -> _SupplyBuilder:
        self._origin_term = tag
        return self

    def to(self, board: str) -> _EndpointBuilder:
        self._dest_board = board
        self._reg.require_board(board)
        return _EndpointBuilder(self, is_origin=False)

    def with_wire(self, wire: str) -> _SupplyBuilder:
        self._reg.require_wire(wire)
        self._wire = wire
        return self

    def meta(self, **meta: Any) -> _SupplyBuilder:
        self._meta.update(meta)
        return self

    def done(self) -> Network:
        if self._dest_board is None:
            raise ValueError("Falta .to(<BOARD_DESTINO>)")

        if self._wire is None:
            raise ValueError("Falta .with_wire(<WIRE_ID>)")

        if self._origin_col is None and self._origin_prot is None and self._origin_term is None:
            raise ValueError(
                "Origen inválido: debe definir .column(...) y/o .protection(...) y/o .terminal(...)"
            )

        if self._dest_col is None and self._dest_prot is None and self._dest_term is None:
            raise ValueError(
                "Destino inválido: debe definir .column(...) y/o .protection(...) y/o .terminal(...)"
            )

        if self._origin_col is not None:
            self._reg.require_column(self._origin_board, self._origin_col)
        if self._origin_term is not None:
            self._reg.require_terminal(self._origin_board, self._origin_term)
        if self._origin_prot is not None:
            self._reg.require_protection(self._origin_board, self._origin_prot)

        assert self._dest_board is not None
        if self._dest_col is not None:
            self._reg.require_column(self._dest_board, self._dest_col)
        if self._dest_term is not None:
            self._reg.require_terminal(self._dest_board, self._dest_term)
        if self._dest_prot is not None:
            self._reg.require_protection(self._dest_board, self._dest_prot)

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
            SupplyLinkRef(origin=origin, destination=dest, wire=self._wire, meta=self._meta)
        )
        return self._net


class Network:
    def __init__(self, registry: Registry) -> None:
        self.registry: Registry = registry
        self.links: list[SupplyLinkRef] = []

    def supply_from(self, board: str) -> _SupplyBuilder:
        return _SupplyBuilder(self, board)
