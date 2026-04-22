# src/elecgenflow/ingest/network_compiler.py
from __future__ import annotations

from typing import Any, cast

from .errors import InvalidLinkError, MissingTagError
from .payload_models import EndpointSnapshot, NetworkLinkSnapshot
from .registry_bootstrap import RegistryIndex


def _has_any_selector(ep: dict[str, Any]) -> bool:
    return bool(ep.get("column") or ep.get("protection") or ep.get("terminal"))


def _is_assembly(reg: RegistryIndex, name: str) -> bool:
    return name in reg.assembly_columns


def _resolve_origin_board_if_assembly(
    origin: dict[str, Any], reg: RegistryIndex
) -> tuple[str, dict[str, Any]]:
    ob = origin.get("board")
    if not isinstance(ob, str) or not ob:
        raise InvalidLinkError("origin.board faltante")

    if not _is_assembly(reg, ob):
        return ob, origin

    col = origin.get("column")
    if not isinstance(col, str) or not col:
        raise InvalidLinkError(f"Origen es ensamble '{ob}' pero no definiste .column('COL-xx')")

    if (ob, col) not in reg.columns:
        raise MissingTagError(f"Columna origen inexistente: {ob}:{col}")

    board_real = reg.assembly_columns.get(ob, {}).get(col)
    if not board_real:
        raise MissingTagError(f"No se pudo resolver columna {ob}:{col} a un board real")

    origin2 = dict(origin)
    origin2["board"] = board_real
    origin2["column"] = col
    return board_real, origin2


def compile_network(
    links: list[NetworkLinkSnapshot], reg: RegistryIndex
) -> list[NetworkLinkSnapshot]:
    compiled: list[NetworkLinkSnapshot] = []

    for lk in links:
        origin = dict(lk.get("origin") or {})
        dest = dict(lk.get("destination") or {})

        if not isinstance(origin.get("board"), str) or not origin.get("board"):
            raise InvalidLinkError("Link inválido: origin.board faltante")
        if not isinstance(dest.get("board"), str) or not dest.get("board"):
            raise InvalidLinkError("Link inválido: destination.board faltante")

        if not _has_any_selector(origin):
            raise InvalidLinkError(
                f"Origen inválido ({origin.get('board')}): debe definir column() y/o protection() y/o terminal()"
            )
        if not _has_any_selector(dest):
            raise InvalidLinkError(
                f"Destino inválido ({dest.get('board')}): debe definir column() y/o protection() y/o terminal()"
            )

        wire = lk.get("wire")
        if not isinstance(wire, str) or not wire:
            raise InvalidLinkError("Link inválido: wire faltante")

        meta = dict(lk.get("meta") or {})
        meta["compiled"] = True

        origin_board_before = str(origin["board"])
        origin_board_real, origin = _resolve_origin_board_if_assembly(origin, reg)

        if origin_board_before != origin_board_real:
            meta["origin_assembly"] = origin_board_before
            meta["origin_column"] = origin.get("column")
            meta["origin_column_board"] = origin_board_real

        if origin_board_real not in reg.boards and origin_board_real not in reg.in_service_boards:
            raise MissingTagError(f"Board origen inexistente: {origin_board_real}")

        dest_board = str(dest["board"])
        if (
            dest_board not in reg.boards
            and dest_board not in reg.in_service_boards
            and dest_board not in reg.out_of_service_boards
        ):
            raise MissingTagError(f"Board destino inexistente: {dest_board}")

        # SIM102: single if (endpoint origin)
        oprot = origin.get("protection")
        if (
            isinstance(oprot, str)
            and oprot
            and (origin_board_real, oprot) not in reg.protections_end
        ):
            raise MissingTagError(
                f"Protección ORIGEN (endpoint) inexistente: {origin_board_real}:{oprot}"
            )

        # SIM102: single if (entrypoint destination)
        dprot = dest.get("protection")
        if isinstance(dprot, str) and dprot and (dest_board, dprot) not in reg.protections_entry:
            raise MissingTagError(
                f"Protección DESTINO (entrypoint) inexistente: {dest_board}:{dprot}"
            )

        compiled.append(
            {
                "origin": cast(EndpointSnapshot, dict(origin)),
                "destination": cast(EndpointSnapshot, dict(dest)),
                "wire": wire,
                "meta": meta,
            }
        )

    return compiled
