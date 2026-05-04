# examples/Ford_BsAs_Pachecho/Boards/TGBT/tgbt_col03.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("TGBT_COL03")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=800, kA=50))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=800, slots=18)
        # Estos tags existen porque el Network los usa como origin.protection("Qxx")
        .add_circuit(tag="Q59", protection="MCCB", load="0kVA", type="feeder", phases=3, desc="Feeder TS_LITE_01")
        .add_circuit(tag="Q60", protection="MCCB", load="0kVA", type="feeder", phases=3, desc="Feeder TS_LITE_02")
        .add_circuit(tag="Q61", protection="MCCB", load="0kVA", type="feeder", phases=3, desc="Feeder TS_POWR_01")
        .add_circuit(tag="Q62", protection="MCCB", load="0kVA", type="feeder", phases=3, desc="Feeder TS_POWR_02")
        .build("Schneider Electric")
    )