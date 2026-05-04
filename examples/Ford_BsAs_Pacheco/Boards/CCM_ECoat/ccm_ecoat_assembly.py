# examples/Ford_BsAs_Pachecho/Boards/CCM_Ecoat/ccm_ecoat_assembly.py

from __future__ import annotations

from electro_core import CCM


def build_assemblies():
    return [
        CCM.assembly("CCM_ECOAT")
        .built_with(switchgear="Schneider Electric", enclosure="Prisma", busbar_material="COBRE")
        .main_busbar(capacity=2500, coating="PAINTED", segregation="2b")
        .add_column(index=1, board="CCM_ECOAT_COL01")
        .add_column(index=2, board="CCM_ECOAT_COL02")
        .add_column(index=3, board="CCM_ECOAT_COL03")
        .build()
        .in_service()
    ]