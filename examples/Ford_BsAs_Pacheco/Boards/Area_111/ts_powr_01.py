# examples/Ford_BsAs_Pachecho/Boards/Area_111/ts_powr_01.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("TS_POWR_01")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=250, kA=36))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=400, slots=12)
        .add_circuit(tag="M1", protection="MCCB", load="40HP", type="motor", phases=3, desc="Motor 3φ")
        .add_circuit(tag="M2", protection="MCCB", load="22kW", type="motor", phases=3, desc="Motor 3φ")
        .add_circuit(tag="A1", protection="MCB", load="5kVA", type="generic", phases=1, desc="Aux 1φ")
        .build("Schneider Electric")
    )




