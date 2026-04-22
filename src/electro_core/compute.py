# src/electro_core/compute.py
from __future__ import annotations

from dataclasses import asdict
from typing import Any


def board_local_load_kw(net: Any, board_name: str) -> float:
    """
    Duck-typing:
    - net.boards[board_name] existe
    - board.circuits iterable
    - circuit.power_kw property OR circuit.params["power_kw"]
    """
    b = net.boards[board_name]
    total = 0.0
    for c in getattr(b, "circuits", []):
        if hasattr(c, "power_kw"):
            total += float(c.power_kw)
        else:
            params = getattr(c, "params", {}) or {}
            total += float(params.get("power_kw", 0.0))
    return total


def downstream_map(net: Any) -> dict[str, list[str]]:
    m: dict[str, list[str]] = {}
    for lk in getattr(net, "links", []):
        m.setdefault(lk.from_board, []).append(lk.to_board)
    return m


def total_board_load_kw(net: Any, board_name: str) -> float:
    dm = downstream_map(net)

    def rec(bn: str, visiting: set[str]) -> float:
        if bn in visiting:
            raise ValueError(f"Ciclo detectado en la red: {bn}")
        visiting.add(bn)

        total = board_local_load_kw(net, bn)
        for child in dm.get(bn, []):
            total += rec(child, visiting)

        visiting.remove(bn)
        return total

    return rec(board_name, set())


def cable_context(net: Any, link_name: str) -> dict[str, Any]:
    lk = next(x for x in getattr(net, "links", []) if x.name == link_name)
    load_kw = total_board_load_kw(net, lk.to_board)

    import math

    v_line = 380.0
    pf = 0.9
    current_a = (load_kw * 1000) / (math.sqrt(3) * v_line * pf) if load_kw > 0 else 0.0

    suggested = getattr(lk.cable_hint, "section_mm2", None) or (
        25 if current_a <= 63 else 50 if current_a <= 100 else 95
    )

    return {
        "link": lk.name,
        "from": lk.from_board,
        "to": lk.to_board,
        "downstream_load_kw": round(load_kw, 3),
        "estimated_current_a": round(current_a, 2),
        "upstream_protection": {
            "kind": lk.upstream_protection.kind,
            **lk.upstream_protection.params,
        },
        "cable_hint": asdict(lk.cable_hint),
        "suggested_section_mm2": suggested,
        "meta": lk.meta,
    }
