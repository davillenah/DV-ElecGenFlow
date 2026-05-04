# examples/Ford_BsAs_Pachecho/Boards/TGBT/tgbt_col01.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("TGBT_COL01")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=800, kA=50))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=800, slots=12)
        .add_circuit(tag="Q10", protection="MCCB", load="0kVA", type="feeder", phases=3, desc="Spare feeder")
        .build("Schneider Electric")
    )




