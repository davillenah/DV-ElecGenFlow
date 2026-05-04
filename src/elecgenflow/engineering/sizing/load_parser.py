# src/elecgenflow/engineering/sizing/load_parser.py

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LoadSpec:
    """
    Representa una carga en forma normalizada.

    Preferimos apparent_power_kva cuando exista (más robusto).
    Si solo hay power_kw, el cálculo de corriente necesitará cosφ (si no hay, el motor debe definir política).
    """

    apparent_power_kva: float | None = None
    power_kw: float | None = None
    current_a: float | None = None
    note: str = ""


_NUM_UNIT_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)\s*$")


def parse_load(value: str | float | int | None) -> LoadSpec | None:
    """
    Parseo tolerante:
      - "22kVA", "15kva", "37kW", "10A"
      - float/int: se interpreta como kW por defecto (política conservadora, se deja nota)
      - None: sin carga declarada
    """
    if value is None:
        return None

    if isinstance(value, int | float):
        # Política: si viene número “pelado”, lo tratamos como kW (común en declaraciones rápidas)
        return LoadSpec(power_kw=float(value), note="Numeric load assumed as kW (no unit).")

    s = str(value).strip()
    if not s:
        return None

    m = _NUM_UNIT_RE.match(s)
    if not m:
        # Si no parsea, lo devolvemos como “no reconocido”
        return LoadSpec(note=f"Unparsed load format: {s}")

    num = float(m.group(1))
    unit = m.group(2).strip().upper()

    if unit in ("KVA",):
        return LoadSpec(apparent_power_kva=num)
    if unit in ("KW",):
        return LoadSpec(power_kw=num)
    if unit in ("A", "AMP", "AMPS"):
        return LoadSpec(current_a=num)

    # Extensible: HP, VA, W, etc.
    return LoadSpec(note=f"Unknown unit '{unit}' in load: {s}")
