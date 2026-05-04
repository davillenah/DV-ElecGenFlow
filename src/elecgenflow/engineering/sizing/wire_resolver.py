# src/elecgenflow/engineering/sizing/wire_resolver.py

from __future__ import annotations

from typing import Any

from elecgenflow.engineering.catalog.methods import CableForm, InstallationRefMethod, PhaseSystem

from .wire_spec import WireSpec


def _norm_conductor(x: str) -> str:
    x = str(x).strip().upper()
    if x in ("AL", "ALUMINIO", "ALUMINUM"):
        return "AL"
    if x in ("CU", "COBRE", "COPPER"):
        return "CU"
    return x


def _norm_insulation(x: str) -> str:
    return str(x).strip().upper()


def _norm_method(x: str) -> InstallationRefMethod:
    return InstallationRefMethod(str(x).strip().upper())


def build_wire_spec_from_link(
    link: dict[str, Any],
    *,
    phase_system: PhaseSystem,
    default_ambient_c: float = 40.0,
) -> WireSpec | None:
    """
    Construye WireSpec a partir de un NetworkLinkSnapshot (dict).

    Se apoya en lo que declarás en DSL:
      - wire_id (lk["wire"] o similar)
      - configured_as: multipolar/unipolar
      - insulation, conductor, installed_in

    Si falta info clave, devuelve None (para que el motor decida fallback).
    """
    wire_id = link.get("wire") or link.get("wire_id") or link.get("id")
    if not isinstance(wire_id, str) or not wire_id:
        return None

    cfg = link.get("wire_config") or link.get("config") or link.get("configured_as") or {}
    if not isinstance(cfg, dict):
        cfg = {}

    # Forma del cable
    form_raw = cfg.get("form") or cfg.get("cable_form") or cfg.get("multipolar")
    if form_raw is True:
        cable_form = CableForm.MULTIPOLAR
    elif form_raw is False:
        cable_form = CableForm.UNIPOLAR
    else:
        # Si viene string
        s = str(form_raw).strip().upper()
        cable_form = (
            CableForm.MULTIPOLAR
            if s in ("MULTIPOLAR", "MULTI", "TRUE")
            else CableForm.UNIPOLAR
            if s in ("UNIPOLAR", "UNI")
            else CableForm.MULTIPOLAR
        )

    insulation = _norm_insulation(cfg.get("insulation", "PVC"))
    conductor = _norm_conductor(cfg.get("conductor", "CU"))
    method = _norm_method(cfg.get("installed_in", cfg.get("method", "E")))

    include_prot = bool(
        cfg.get("with_protection_cable_included", cfg.get("include_protection_cable", False))
    )

    ambient = float(cfg.get("ambient_air_c", default_ambient_c))
    grouped = int(cfg.get("grouped_circuits", 1))
    soil = cfg.get("soil_resistivity")
    depth = cfg.get("burial_depth_m")

    return WireSpec(
        wire_id=wire_id,
        phase_system=phase_system,
        cable_form=cable_form,
        conductor=conductor,
        insulation=insulation,
        method=method,
        include_protection_cable=include_prot,
        ambient_air_c=ambient,
        grouped_circuits=grouped,
        soil_resistivity=float(soil) if soil is not None else None,
        burial_depth_m=float(depth) if depth is not None else None,
    )
