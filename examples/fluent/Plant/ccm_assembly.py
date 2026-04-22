# MyProject/Plant/ccm_assembly.py
from electro_core import TGBT

def build_assemblies():
    return [
        TGBT.assembly("TGBT-GENERAL")
            .built_with(
                switchgear="Schneider Electric",
                enclosure="PrismaSet P",
                busbar_material="COBRE",
            )
            .main_busbar(capacity=4000, coating="PAINTED", segregation="4b")
            .add_column(index=1, board="TGBT-COL-01")
            .add_column(index=3, board="TGBT-COL-03")
            .build()
            .in_service()
    ]