from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .payload_models import AssemblySnapshot, BoardSnapshot, NetworkLinkSnapshot

ENTRYPOINT_TAG = "IG"  # default legacy si no hay tag explícito


@dataclass
class RegistryIndex:
    boards: set[str] = field(default_factory=set)
    columns: set[tuple[str, str]] = field(default_factory=set)  # (owner, col)

    protections_entry: set[tuple[str, str]] = field(default_factory=set)  # (board, tag)
    protections_end: set[tuple[str, str]] = field(default_factory=set)  # (board, tag)

    terminals: set[tuple[str, str]] = field(default_factory=set)
    wires: set[str] = field(default_factory=set)

    in_service_boards: set[str] = field(default_factory=set)
    out_of_service_boards: set[str] = field(default_factory=set)

    assembly_columns: dict[str, dict[str, str]] = field(default_factory=dict)
    # assembly_columns[assembly]["COL-03"] = board_tag


def _iter_circuits(board: BoardSnapshot) -> list[dict[str, Any]]:
    buses = board.get("buses") or []
    circuits: list[dict[str, Any]] = []
    for b in buses:
        circuits.extend(b.get("circuits") or [])
    return circuits


def _infer_endpoints_from_buses(board_name: str, snap: BoardSnapshot, reg: RegistryIndex) -> None:
    mp = snap.get("main_protection") or {}
    if isinstance(mp, dict) and mp:
        tag_any = mp.get("tag", ENTRYPOINT_TAG)
        tag = tag_any if isinstance(tag_any, str) and tag_any else ENTRYPOINT_TAG
        reg.protections_entry.add((board_name, tag))

    for c in _iter_circuits(snap):
        ctag = c.get("tag")
        prot = c.get("protection")
        if ctag and prot:
            reg.protections_end.add((board_name, str(ctag)))

        subs = c.get("subcircuits") or []
        parent_tag = str(ctag) if ctag else ""
        for sc in subs:
            stag = sc.get("tag")
            sprot = sc.get("protection")
            if parent_tag and stag and sprot:
                reg.protections_end.add((board_name, f"{parent_tag}:{stag}"))


def bootstrap_registry(
    boards_by_name: dict[str, BoardSnapshot],
    assemblies: list[AssemblySnapshot],
    network_links: list[NetworkLinkSnapshot],
) -> RegistryIndex:
    reg = RegistryIndex()

    for name in boards_by_name:
        reg.boards.add(name)

    for asm in assemblies:
        asm_name = str(asm.get("name"))
        reg.boards.add(asm_name)
        reg.assembly_columns.setdefault(asm_name, {})

        cols = asm.get("columns") or []
        for c in cols:
            idx_raw = c.get("index")
            if idx_raw is None:
                raise ValueError(f"Assembly '{asm_name}' column sin index: {c}")
            idx = int(idx_raw)

            board_tag_raw = c.get("board")
            if not isinstance(board_tag_raw, str) or not board_tag_raw:
                raise ValueError(f"Assembly '{asm_name}' column sin board válido: {c}")
            board_tag = board_tag_raw

            col_tag = f"COL-{idx:02d}"
            reg.columns.add((asm_name, col_tag))
            reg.assembly_columns[asm_name][col_tag] = board_tag
            reg.in_service_boards.add(board_tag)

    for board_name, snap in boards_by_name.items():
        endpoints = snap.get("endpoints")

        if isinstance(endpoints, list) and endpoints:
            for e in endpoints:
                role = e.get("role")
                kind = e.get("kind")
                tag = e.get("tag")

                if kind == "protection" and isinstance(tag, str) and tag:
                    if role == "entrypoint":
                        reg.protections_entry.add((board_name, tag))
                    elif role == "endpoint":
                        reg.protections_end.add((board_name, tag))

                if kind == "terminal" and isinstance(tag, str) and tag:
                    reg.terminals.add((board_name, tag))

                if kind == "column" and isinstance(tag, str) and tag:
                    reg.columns.add((board_name, tag))
        else:
            _infer_endpoints_from_buses(board_name, snap, reg)

    for lk in network_links:
        o = lk.get("origin") or {}
        d = lk.get("destination") or {}
        ob = o.get("board")
        db = d.get("board")

        if isinstance(ob, str) and ob:
            reg.in_service_boards.add(ob)
        if isinstance(db, str) and db:
            reg.in_service_boards.add(db)

        wire = lk.get("wire")
        if isinstance(wire, str) and wire:
            reg.wires.add(wire)

    reg.out_of_service_boards = set(reg.boards) - set(reg.in_service_boards)
    return reg
