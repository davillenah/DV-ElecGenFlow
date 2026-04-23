from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, cast

from .payload_models import EndpointSnapshot, NetworkLinkSnapshot
from .registry_bootstrap import RegistryIndex

Mode = Literal["dev", "runtime"]
Severity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class CompileIssue:
    code: str
    severity: Severity
    message: str
    context: dict[str, str] = field(default_factory=dict)


@dataclass
class CompileReport:
    mode: Mode
    compiled: int = 0
    skipped: int = 0
    issues: list[CompileIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)


def _has_any_selector(ep: dict[str, Any]) -> bool:
    return bool(ep.get("column") or ep.get("protection") or ep.get("terminal"))


def _is_assembly(reg: RegistryIndex, name: str) -> bool:
    return name in reg.assembly_columns


def _resolve_origin_board_if_assembly(
    origin: dict[str, Any], reg: RegistryIndex, report: CompileReport
) -> tuple[str, dict[str, Any], str | None]:
    ob = origin.get("board")
    if not isinstance(ob, str) or not ob:
        return "", origin, None

    if not _is_assembly(reg, ob):
        return ob, origin, None

    col = origin.get("column")
    if not isinstance(col, str) or not col:
        report.issues.append(
            CompileIssue(
                code="ORIGIN_ASSEMBLY_MISSING_COLUMN",
                severity="error" if report.mode == "dev" else "warning",
                message=f"Origen assembly '{ob}' requiere column('COL-xx')",
                context={"assembly": ob},
            )
        )
        reg.disabled_boards.add(ob)
        return ob, origin, ob

    if (ob, col) not in reg.columns:
        report.issues.append(
            CompileIssue(
                code="ORIGIN_COLUMN_MISSING",
                severity="error" if report.mode == "dev" else "warning",
                message=f"Columna origen inexistente: {ob}:{col}",
                context={"assembly": ob, "column": col},
            )
        )
        reg.disabled_columns.add((ob, col))
        return ob, origin, ob

    board_real = reg.assembly_columns.get(ob, {}).get(col)
    if not board_real:
        report.issues.append(
            CompileIssue(
                code="ORIGIN_COLUMN_UNRESOLVED",
                severity="error" if report.mode == "dev" else "warning",
                message=f"No se pudo resolver columna {ob}:{col} a un board real",
                context={"assembly": ob, "column": col},
            )
        )
        reg.disabled_columns.add((ob, col))
        return ob, origin, ob

    origin2 = dict(origin)
    origin2["board"] = board_real
    origin2["column"] = col
    return board_real, origin2, ob


def compile_network(
    links: list[NetworkLinkSnapshot],
    reg: RegistryIndex,
    *,
    mode: Mode = "dev",
) -> tuple[list[NetworkLinkSnapshot], CompileReport]:
    report = CompileReport(mode=mode)
    compiled: list[NetworkLinkSnapshot] = []

    for lk in links:
        origin = dict(lk.get("origin") or {})
        dest = dict(lk.get("destination") or {})
        wire = lk.get("wire")
        meta = dict(lk.get("meta") or {})

        if not isinstance(wire, str) or not wire:
            report.issues.append(
                CompileIssue(
                    code="WIRE_MISSING",
                    severity="error" if mode == "dev" else "warning",
                    message="Link inválido: wire faltante",
                )
            )
            report.skipped += 1
            continue

        ob_any = origin.get("board")
        if not isinstance(ob_any, str) or not ob_any:
            report.issues.append(
                CompileIssue(
                    code="ORIGIN_BOARD_MISSING",
                    severity="error" if mode == "dev" else "warning",
                    message="Link inválido: origin.board faltante",
                )
            )
            report.skipped += 1
            continue

        db_any = dest.get("board")
        load_any = dest.get("load")
        has_dest_board = isinstance(db_any, str) and bool(db_any)
        has_dest_load = isinstance(load_any, str) and bool(load_any)

        if not has_dest_board and not has_dest_load:
            report.issues.append(
                CompileIssue(
                    code="DESTINATION_MISSING",
                    severity="error" if mode == "dev" else "warning",
                    message="Link inválido: destination.board o destination.load faltante",
                )
            )
            report.skipped += 1
            continue

        if not _has_any_selector(origin):
            report.issues.append(
                CompileIssue(
                    code="ORIGIN_NO_SELECTOR",
                    severity="error" if mode == "dev" else "warning",
                    message=f"Origen inválido ({ob_any}): debe definir column/protection/terminal",
                    context={"board": ob_any},
                )
            )
            report.skipped += 1
            continue

        if has_dest_board and not _has_any_selector(dest):
            report.issues.append(
                CompileIssue(
                    code="DEST_NO_SELECTOR",
                    severity="error" if mode == "dev" else "warning",
                    message=f"Destino inválido ({db_any}): debe definir column/protection/terminal",
                    context={"board": str(db_any)},
                )
            )
            report.skipped += 1
            continue

        origin_board_before = str(ob_any)
        origin_board_real, origin, origin_asm = _resolve_origin_board_if_assembly(
            origin, reg, report
        )

        if (
            origin_asm is not None
            and origin_board_real
            and origin_board_real != origin_board_before
        ):
            meta["origin_assembly"] = origin_asm
            meta["origin_column"] = origin.get("column")
            meta["origin_column_board"] = origin_board_real

        if origin_board_real not in reg.boards and origin_board_real not in reg.in_service_boards:
            report.issues.append(
                CompileIssue(
                    code="ORIGIN_BOARD_UNKNOWN",
                    severity="error" if mode == "dev" else "warning",
                    message=f"Board origen inexistente: {origin_board_real}",
                    context={"board": origin_board_real},
                )
            )
            reg.disabled_boards.add(origin_board_real)
            report.skipped += 1
            continue

        dest_board = str(db_any) if has_dest_board else ""
        if (
            has_dest_board
            and dest_board not in reg.boards
            and dest_board not in reg.in_service_boards
            and dest_board not in reg.out_of_service_boards
        ):
            report.issues.append(
                CompileIssue(
                    code="DEST_BOARD_UNKNOWN",
                    severity="error" if mode == "dev" else "warning",
                    message=f"Board destino inexistente: {dest_board}",
                    context={"board": dest_board},
                )
            )
            reg.disabled_boards.add(dest_board)
            report.skipped += 1
            continue

        oprot = origin.get("protection")
        if (
            isinstance(oprot, str)
            and oprot
            and (origin_board_real, oprot) not in reg.protections_end
        ):
            report.issues.append(
                CompileIssue(
                    code="ORIGIN_ENDPOINT_UNKNOWN",
                    severity="error" if mode == "dev" else "warning",
                    message=f"Protección ORIGEN (endpoint) inexistente: {origin_board_real}:{oprot}",
                    context={"board": origin_board_real, "protection": oprot},
                )
            )
            reg.disabled_endpoints.add((origin_board_real, oprot))
            report.skipped += 1
            continue

        if has_dest_board:
            dprot = dest.get("protection")
            if (
                isinstance(dprot, str)
                and dprot
                and (dest_board, dprot) not in reg.protections_entry
            ):
                report.issues.append(
                    CompileIssue(
                        code="DEST_ENTRYPOINT_UNKNOWN",
                        severity="error" if mode == "dev" else "warning",
                        message=f"Protección DESTINO (entrypoint) inexistente: {dest_board}:{dprot}",
                        context={"board": dest_board, "protection": dprot},
                    )
                )
                reg.disabled_entrypoints.add((dest_board, dprot))
                report.skipped += 1
                continue

        oterm = origin.get("terminal")
        if isinstance(oterm, str) and oterm and (origin_board_real, oterm) not in reg.terminals:
            report.issues.append(
                CompileIssue(
                    code="ORIGIN_TERMINAL_UNKNOWN",
                    severity="error" if mode == "dev" else "warning",
                    message=f"Terminal origen inexistente: {origin_board_real}:{oterm}",
                    context={"board": origin_board_real, "terminal": oterm},
                )
            )
            reg.disabled_terminals.add((origin_board_real, oterm))
            report.skipped += 1
            continue

        if has_dest_board:
            dterm = dest.get("terminal")
            if isinstance(dterm, str) and dterm and (dest_board, dterm) not in reg.terminals:
                report.issues.append(
                    CompileIssue(
                        code="DEST_TERMINAL_UNKNOWN",
                        severity="error" if mode == "dev" else "warning",
                        message=f"Terminal destino inexistente: {dest_board}:{dterm}",
                        context={"board": dest_board, "terminal": dterm},
                    )
                )
                reg.disabled_terminals.add((dest_board, dterm))
                report.skipped += 1
                continue

        if has_dest_load:
            ld = str(load_any)
            if ld:
                reg.loads.add(ld)

        meta["compiled"] = True

        compiled.append(
            {
                "origin": cast(EndpointSnapshot, dict(origin)),
                "destination": cast(EndpointSnapshot, dict(dest)),
                "wire": wire,
                "meta": meta,
            }
        )
        report.compiled += 1

    return compiled, report
