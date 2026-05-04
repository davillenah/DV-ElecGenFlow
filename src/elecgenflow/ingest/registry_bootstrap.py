# src/elecgenflow/ingest/registry_bootstrap.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .payload_models import AssemblySnapshot, BoardSnapshot, NetworkLinkSnapshot

# Tag por defecto para el “entrypoint” (protección principal) cuando no viene explícito.
ENTRYPOINT_TAG = "IG"


@dataclass
class RegistryIndex:
    """
    Índice “rápido” para inferir y validar entidades del proyecto a partir de snapshots:
      - boards/columns/terminales/protecciones/wires/loads
      - in_service / out_of_service
      - degradación runtime (no bloqueante)
    """

    boards: set[str] = field(default_factory=set)
    columns: set[tuple[str, str]] = field(default_factory=set)  # (owner, col)

    protections_entry: set[tuple[str, str]] = field(default_factory=set)  # (board, tag)
    protections_end: set[tuple[str, str]] = field(default_factory=set)  # (board, tag)

    terminals: set[tuple[str, str]] = field(default_factory=set)  # (board, terminal_tag)
    wires: set[str] = field(default_factory=set)

    loads: set[str] = field(default_factory=set)  # cargas finales (virtuales)

    in_service_boards: set[str] = field(default_factory=set)
    out_of_service_boards: set[str] = field(default_factory=set)

    # assembly -> { "COL-01": "BoardName", ... }
    assembly_columns: dict[str, dict[str, str]] = field(default_factory=dict)

    # runtime degradation (no bloqueante)
    disabled_boards: set[str] = field(default_factory=set)
    disabled_columns: set[tuple[str, str]] = field(default_factory=set)  # (assembly, col)
    disabled_endpoints: set[tuple[str, str]] = field(default_factory=set)  # (board, prot)
    disabled_entrypoints: set[tuple[str, str]] = field(default_factory=set)  # (board, prot)
    disabled_terminals: set[tuple[str, str]] = field(default_factory=set)  # (board, terminal)
    disabled_loads: set[str] = field(default_factory=set)


def _iter_circuits(board: BoardSnapshot) -> list[dict[str, Any]]:
    """
    Extrae todos los circuitos declarados en buses, incluyendo subcircuits.
    """
    buses = board.get("buses") or []
    circuits: list[dict[str, Any]] = []
    for b in buses:
        circuits.extend(b.get("circuits") or [])
    return circuits


def _infer_endpoints_from_buses(board_name: str, snap: BoardSnapshot, reg: RegistryIndex) -> None:
    """
    Fallback cuando el board snapshot no trae lista explícita de 'endpoints'.
    Infiera:
      - entrypoint: main_protection (si existe)
      - endpoints: protections en circuitos y subcircuits (si existen)
    """
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
    """
    Construye un índice de entidades presentes en:
      - boards_by_name (tableros)
      - assemblies (armados/columnas)
      - network_links (conexiones/cables/cargas)

    Nota:
      - Este módulo NO debe construir catálogos técnicos (ampacidad/derating/RX).
        Eso corresponde al Core/Engine bootstrap (p.ej. core/catalog_provider.py) y
        se inyecta al motor de dimensionamiento desde el inicializador del proyecto.
    """
    reg = RegistryIndex()

    # 1) boards “declarados” explícitamente
    for name in boards_by_name:
        if isinstance(name, str) and name:
            reg.boards.add(name)

    # 2) assemblies → columnas + boards en servicio
    for asm in assemblies:
        asm_name = str(asm.get("name"))
        if not asm_name:
            continue

        reg.boards.add(asm_name)
        reg.assembly_columns.setdefault(asm_name, {})

        cols = asm.get("columns") or []
        for c in cols:
            idx_raw = c.get("index")
            if idx_raw is None:
                continue
            try:
                idx = int(idx_raw)
            except (TypeError, ValueError):
                continue

            board_tag_raw = c.get("board")
            if not isinstance(board_tag_raw, str) or not board_tag_raw:
                continue
            board_tag = board_tag_raw

            col_tag = f"COL-{idx:02d}"
            reg.columns.add((asm_name, col_tag))
            reg.assembly_columns[asm_name][col_tag] = board_tag
            reg.in_service_boards.add(board_tag)

    # 3) boards → endpoints/entrypoints/terminales/columnas (si vienen explícitos)
    for board_name, snap in boards_by_name.items():
        endpoints = snap.get("endpoints")

        if isinstance(endpoints, list) and endpoints:
            for e in endpoints:
                if not isinstance(e, dict):
                    continue

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
            # Fallback: inferir desde buses/circuitos
            _infer_endpoints_from_buses(board_name, snap, reg)

    # 4) network links → in_service + wires + loads
    for lk in network_links:
        o = lk.get("origin") or {}
        d = lk.get("destination") or {}

        ob = o.get("board")
        db = d.get("board")
        ld = d.get("load")

        if isinstance(ob, str) and ob:
            reg.in_service_boards.add(ob)
        if isinstance(db, str) and db:
            reg.in_service_boards.add(db)

        if isinstance(ld, str) and ld:
            reg.loads.add(ld)

        wire = lk.get("wire")
        if isinstance(wire, str) and wire:
            reg.wires.add(wire)

    # 5) boards fuera de servicio = declarados - en servicio
    reg.out_of_service_boards = set(reg.boards) - set(reg.in_service_boards)
    return reg
