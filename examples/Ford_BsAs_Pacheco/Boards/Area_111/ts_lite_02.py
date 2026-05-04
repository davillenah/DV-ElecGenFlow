# examples/Ford_BsAs_Pachecho/Boards/Area_111/ts_lite_02.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("TS_LITE_02")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=160, kA=25))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=250, slots=12)
        .add_circuit(tag="L3", protection="MCB", load="10kVA", type="lite", phases=1, desc="Iluminación 1φ")
        .add_circuit(tag="L4", protection="MCB", load="2kW", type="lite", phases=1, desc="Servicios 1φ")
        .build("Schneider Electric")
    )




