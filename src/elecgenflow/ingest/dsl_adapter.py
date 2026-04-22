# src/elecgenflow/ingest/dsl_adapter.py
from __future__ import annotations

from uuid import uuid4

from elecgenflow.elecboard.ir import Board, Branch, ElecboardIR, Load, Node
from elecgenflow.elecboard.types import (
    BoardLevel,
    BranchKind,
    LoadKind,
    NodeKind,
    Phase,
    TopologyKind,
)

from .payload_models import BoardSnapshot, NetworkLinkSnapshot
from .registry_bootstrap import RegistryIndex


def _board_id(name: str) -> str:
    return f"B:{name}"


def _node_id(board: str, kind: str, tag: str) -> str:
    return f"N:{board}:{kind}:{tag}"


def _load_kind(kind: str) -> LoadKind:
    k = (kind or "").lower()
    if k in ("lighting", "lite"):
        return LoadKind.LIGHTING
    if k == "motor":
        return LoadKind.MOTOR
    if k == "hvac":
        return LoadKind.HVAC
    return LoadKind.GENERIC


def build_elecboard_ir(
    boards_by_name: dict[str, BoardSnapshot],
    reg: RegistryIndex,
    compiled_links: list[NetworkLinkSnapshot],
) -> ElecboardIR:
    active_boards = sorted(reg.in_service_boards)

    boards: list[Board] = []
    nodes: list[Node] = []
    branches: list[Branch] = []
    loads: list[Load] = []

    lv_phases = {Phase.L1, Phase.L2, Phase.L3, Phase.N, Phase.PE}

    # Index entrypoints por board
    entrypoints_by_board: dict[str, list[str]] = {}
    for b, tag in reg.protections_entry:
        entrypoints_by_board.setdefault(b, []).append(tag)

    for bname in active_boards:
        snap = boards_by_name.get(bname)
        if snap is None:
            continue

        bid = _board_id(bname)

        bus = _node_id(bname, "BUS", "MAIN")
        node_ids = [bus]

        # ✅ crear TODOS los entrypoints definidos para este board
        for ep_tag in sorted(entrypoints_by_board.get(bname, [])):
            ep_node = _node_id(bname, "ENTRY", ep_tag)
            node_ids.append(ep_node)
            branches.append(
                Branch(
                    branch_id=f"BR:{uuid4().hex}",
                    from_node=bus,
                    to_node=ep_node,
                    kind=BranchKind.INTERNAL,
                    phases=set(lv_phases),
                    meta={"tag": ep_tag, "role": "entrypoint"},
                )
            )

        # endpoints por circuits/subcircuits
        buses = snap.get("buses") or []
        for bus_snap in buses:
            for c in bus_snap.get("circuits") or []:
                ctag = c.get("tag")
                ctype = c.get("type") or "generic"
                if ctag and (bname, str(ctag)) in reg.protections_end:
                    nid = _node_id(bname, "END", str(ctag))
                    node_ids.append(nid)
                    branches.append(
                        Branch(
                            branch_id=f"BR:{uuid4().hex}",
                            from_node=bus,
                            to_node=nid,
                            kind=BranchKind.INTERNAL,
                            phases=set(lv_phases),
                            meta={"tag": str(ctag), "role": "endpoint"},
                        )
                    )
                    loads.append(
                        Load(
                            load_id=f"L:{uuid4().hex}",
                            node_id=nid,
                            kind=_load_kind(str(ctype)),
                            phases=set(lv_phases),
                            meta={"circuit": c},
                        )
                    )

                parent_tag = str(ctag) if ctag else ""
                for sc in c.get("subcircuits") or []:
                    stag = sc.get("tag")
                    if parent_tag and stag:
                        full = f"{parent_tag}:{stag}"
                        if (bname, full) in reg.protections_end:
                            snid = _node_id(bname, "END", full)
                            node_ids.append(snid)
                            branches.append(
                                Branch(
                                    branch_id=f"BR:{uuid4().hex}",
                                    from_node=bus,
                                    to_node=snid,
                                    kind=BranchKind.INTERNAL,
                                    phases=set(lv_phases),
                                    meta={"tag": full, "role": "endpoint"},
                                )
                            )
                            loads.append(
                                Load(
                                    load_id=f"L:{uuid4().hex}",
                                    node_id=snid,
                                    kind=_load_kind(str(ctype)),
                                    phases=set(lv_phases),
                                    meta={"subcircuit": sc, "parent": ctag},
                                )
                            )

        boards.append(
            Board(
                board_id=bid,
                name=bname,
                level=BoardLevel.LV,
                phases=set(lv_phases),
                node_ids=node_ids,
                meta={"in_service": True},
            )
        )

        nodes.append(
            Node(node_id=bus, board_id=bid, kind=NodeKind.BUS, phases=set(lv_phases), meta={})
        )

        for nid in node_ids:
            if nid == bus:
                continue
            nodes.append(
                Node(
                    node_id=nid,
                    board_id=bid,
                    kind=NodeKind.TERMINAL,
                    phases=set(lv_phases),
                    meta={},
                )
            )

    # Feeder branches
    for lk in compiled_links:
        o = lk["origin"]
        d = lk["destination"]

        ob = str(o["board"])
        db = str(d["board"])
        oprot = o.get("protection")
        dprot = d.get("protection")

        from_tag = str(oprot or o.get("column") or o.get("terminal"))
        to_tag = str(dprot or d.get("column") or d.get("terminal"))

        from_node = _node_id(ob, "END", from_tag)
        to_node = _node_id(db, "ENTRY", to_tag) if dprot else _node_id(db, "END", to_tag)

        branches.append(
            Branch(
                branch_id=f"FEED:{uuid4().hex}",
                from_node=from_node,
                to_node=to_node,
                kind=BranchKind.FEEDER,
                phases=set(lv_phases),
                meta={
                    "wire": lk["wire"],
                    "origin": o,
                    "destination": d,
                    "dsl_meta": lk.get("meta") or {},
                },
            )
        )

    return ElecboardIR(
        boards=boards,
        nodes=nodes,
        branches=branches,
        loads=loads,
        sources=[],
        topology=TopologyKind.UNKNOWN,
        allow_islands=True,
        meta={
            "epic": "04.00",
            "out_of_service_boards": sorted(reg.out_of_service_boards),
        },
    )
