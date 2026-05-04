# examples/Ford_BsAs_Pachecho/Boards/Area_111/ts_powr_02.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("TS_POWR_02")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=250, kA=36))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=400, slots=12)
        .add_circuit(tag="H1", protection="MCCB", load="12kW", type="hvac", phases=3, desc="HVAC 3φ")
        .add_circuit(tag="H2", protection="MCB", load="3000W", type="hvac", phases=1, desc="HVAC 1φ")
        .build("Schneider Electric")
    )