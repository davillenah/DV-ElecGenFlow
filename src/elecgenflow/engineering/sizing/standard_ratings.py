# src/elecgenflow/engineering/sizing/standard_ratings.py

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# Serie típica (IEC / uso industrial) para interruptores.
DEFAULT_DEVICE_RATINGS_A: list[int] = [
    6,
    10,
    16,
    20,
    25,
    32,
    40,
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3200,
    4000,
]


# Secciones normalizadas típicas; incluimos 600 por tu requerimiento
# (aunque el mercado suele usar 630 como estándar grande).
DEFAULT_SECTIONS_MM2: list[float] = [
    1.5,
    2.5,
    4,
    6,
    10,
    16,
    25,
    35,
    50,
    70,
    95,
    120,
    150,
    185,
    240,
    300,
    400,
    500,
    600,
]


@dataclass(frozen=True)
class RatingSelection:
    in_a: int
    reason: str = ""


def select_next_standard_in(
    ib_a: float, ratings: Iterable[int] = DEFAULT_DEVICE_RATINGS_A
) -> RatingSelection:
    """
    Devuelve el primer In normalizado >= Ib.
    """
    for r in ratings:
        if float(r) >= float(ib_a):
            return RatingSelection(
                in_a=int(r), reason=f"Selected next standard rating >= Ib ({ib_a:.2f} A)"
            )
    # Si Ib supera la lista, devolvemos el mayor.
    rr = list(ratings)
    if not rr:
        raise ValueError("No ratings provided")
    return RatingSelection(in_a=int(rr[-1]), reason="Ib exceeds rating list; selected max rating")
