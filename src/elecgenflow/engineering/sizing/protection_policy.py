# src/elecgenflow/engineering/sizing/protection_policy.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtectionSpec:
    """
    Especificación de protección para coordinación en P2.4.

    - device_type: "MCB", "MCCB", "FUSE", etc.
    - in_a: corriente nominal (si None, la seleccionamos automáticamente)
    - i2_a: corriente convencional de disparo (si None, se deduce por policy)
    """

    device_type: str = "MCB"
    in_a: float | None = None
    i2_a: float | None = None


@dataclass(frozen=True)
class ProtectionResolved:
    device_type: str
    in_a: float
    i2_a: float
    notes: str = ""


class ProtectionPolicy:
    """
    Política de cálculo de I2.

    Por defecto (conservador y estándar en coordinación):
      - I2 = 1.45 * In
    Esto vuelve la condición I2 <= 1.45*Iz en: In <= Iz
    si el dispositivo cumple ese convencionalismo.
    """

    def resolve(self, spec: ProtectionSpec, *, fallback_in_a: float) -> ProtectionResolved:
        dev = (spec.device_type or "MCB").strip().upper()
        in_a = float(spec.in_a) if spec.in_a is not None else float(fallback_in_a)

        if spec.i2_a is not None:
            i2_a = float(spec.i2_a)
            return ProtectionResolved(
                device_type=dev, in_a=in_a, i2_a=i2_a, notes="I2 provided explicitly"
            )

        # Default policy:
        # - MCB/MCCB (básico): usamos 1.45*In como convención de coordinación
        i2_a = 1.45 * in_a
        return ProtectionResolved(
            device_type=dev, in_a=in_a, i2_a=i2_a, notes="Default policy: I2=1.45*In"
        )
