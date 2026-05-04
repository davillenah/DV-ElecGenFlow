# examples/Ford_BsAs_Pachecho/Boards/TGBT/tgbt_assembly.py

from __future__ import annotations

from electro_core import TGBT


def build_assemblies():
    return [
        TGBT.assembly("TGBT_GENERAL")
        .built_with(switchgear="Schneider Electric", enclosure="PrismaSet", busbar_material="COBRE")
            .main_busbar(capacity=4000, coating="PAINTED", segregation="4b")
            .add_column(index=1, board="TGBT_COL01")
            .add_column(index=2, board="TGBT_COL02")
            .add_column(index=3, board="TGBT_COL03")
        .build()
        .in_service()
    ]




