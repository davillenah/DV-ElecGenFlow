# src/elecgenflow/engineering/sizing/sizing_engine.py

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import sqrt

from elecgenflow.engineering.catalog.composite_catalog import CableQuery, CompositeCatalog
from elecgenflow.engineering.catalog.methods import CableForm, InstallationRefMethod, PhaseSystem
from elecgenflow.engineering.sizing.protection_policy import (
    ProtectionPolicy,
    ProtectionResolved,
    ProtectionSpec,
)
from elecgenflow.engineering.sizing.standard_ratings import (
    DEFAULT_DEVICE_RATINGS_A,
    DEFAULT_SECTIONS_MM2,
    select_next_standard_in,
)


@dataclass(frozen=True)
class AmpacityChecks:
    ib_a: float
    in_a: float
    i2_a: float
    itab_a: float
    iz_eff_a: float
    ok_ib_le_in_le_iz: bool
    ok_i2_le_145_iz: bool

    @property
    def ok(self) -> bool:
        return self.ok_ib_le_in_le_iz and self.ok_i2_le_145_iz


@dataclass(frozen=True)
class Result:
    ok: bool
    reason: str
    section_mm2: float | None = None
    checks: AmpacityChecks | None = None
    cable_query: CableQuery | None = None
    protection: ProtectionResolved | None = None


def _ib_from_load(
    *,
    phase_system: PhaseSystem,
    load_kva: float | None,
    load_kw: float | None,
    voltage_ll_v: float,
    voltage_ln_v: float,
    power_factor: float,
) -> float:
    pf = power_factor if 0 < power_factor <= 1 else 0.85

    if phase_system == PhaseSystem.THREE_PHASE:
        vll = float(voltage_ll_v) if voltage_ll_v > 0 else 380.0
        if load_kva is not None and load_kva > 0:
            s_va = float(load_kva) * 1000.0
            return s_va / (sqrt(3) * vll)
        p_w = float(load_kw or 0.0) * 1000.0
        return p_w / (sqrt(3) * vll * pf)

    vln = float(voltage_ln_v) if voltage_ln_v > 0 else 220.0
    if load_kva is not None and load_kva > 0:
        s_va = float(load_kva) * 1000.0
        return s_va / vln
    p_w = float(load_kw or 0.0) * 1000.0
    return p_w / (vln * pf)


def _conductor_temp_c_from_insulation(insulation: str) -> float:
    ins = (insulation or "PVC").strip().upper()
    return 70.0 if ins == "PVC" else 90.0


class SizingEngine:
    def __init__(
        self,
        *,
        catalog: CompositeCatalog,
        protection_policy: ProtectionPolicy | None = None,
        default_pf: float = 0.85,
        section_candidates_mm2: Iterable[float] | None = None,
        device_ratings_a: Iterable[int] | None = None,
    ) -> None:
        self.catalog = catalog
        self.policy = protection_policy or ProtectionPolicy()
        self.default_pf = default_pf
        self.sections = list(section_candidates_mm2 or DEFAULT_SECTIONS_MM2)
        self.device_ratings = (
            list(device_ratings_a)
            if device_ratings_a is not None
            else list(DEFAULT_DEVICE_RATINGS_A)
        )

    def size_feeder_ampacity_only(
        self,
        *,
        from_board: str,
        to_board: str,
        wire_id: str,
        method: InstallationRefMethod,
        cable_form: CableForm,
        conductor: str,
        insulation: str,
        phase_system: PhaseSystem,
        load_kva: float | None,
        load_kw: float | None,
        voltage_ll_v: float,
        voltage_ln_v: float,
        ambient_air_c: float = 40.0,
        grouped_circuits: int = 1,
        soil_resistivity: float | None = None,
        burial_depth_m: float | None = None,
        protection: ProtectionSpec | None = None,
    ) -> Result:
        ib = _ib_from_load(
            phase_system=phase_system,
            load_kva=load_kva,
            load_kw=load_kw,
            voltage_ll_v=voltage_ll_v,
            voltage_ln_v=voltage_ln_v,
            power_factor=self.default_pf,
        )
        if ib <= 0:
            return Result(ok=False, reason=f"Ib inválida ({ib:.3f} A). Revisar cargas/voltajes.")

        rating = select_next_standard_in(ib, ratings=self.device_ratings)
        fallback_in = float(rating.in_a)

        prot_spec = protection or ProtectionSpec()
        prot = self.policy.resolve(prot_spec, fallback_in_a=fallback_in)

        conductor_temp_c = _conductor_temp_c_from_insulation(insulation)

        last_err: str = ""
        for s in self.sections:
            q = CableQuery(
                method=method,
                material=conductor,
                insulation=insulation,
                phase_system=phase_system,
                cable_form=cable_form,
                section_mm2=float(s),
                ambient_air_c=float(ambient_air_c),
                grouped_circuits=int(grouped_circuits),
                soil_resistivity=soil_resistivity,
                burial_depth_m=burial_depth_m,
                conductor_temp_c=conductor_temp_c,
            )

            try:
                itab_a, _d, iz = self.catalog.itab_and_iz(q)
            except Exception as exc:
                last_err = f"Catalog miss for section {s}: {exc}"
                continue

            ok1 = ib <= prot.in_a <= iz
            ok2 = prot.i2_a <= 1.45 * iz

            checks = AmpacityChecks(
                ib_a=float(ib),
                in_a=float(prot.in_a),
                i2_a=float(prot.i2_a),
                itab_a=float(itab_a),
                iz_eff_a=float(iz),
                ok_ib_le_in_le_iz=bool(ok1),
                ok_i2_le_145_iz=bool(ok2),
            )

            if checks.ok:
                return Result(
                    ok=True,
                    reason="Selected by ampacity + overload coordination.",
                    section_mm2=float(s),
                    checks=checks,
                    cable_query=q,
                    protection=prot,
                )

            last_err = f"Section {s} fails: Ib={ib:.2f}, In={prot.in_a:.2f}, Iz={iz:.2f}, I2={prot.i2_a:.2f}"

        return Result(ok=False, reason=f"No section meets ampacity/coordination. Last: {last_err}")
