# examples/Ford_BsAs_Pachecho/Boards/Area_111/ts_lite_01.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("TS_LITE_01")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=160, kA=25))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=250, slots=12)
        .add_circuit(tag="L1", protection="MCB", load="8kVA", type="lite", phases=1, desc="Iluminación 1φ")
        .add_circuit(tag="L2", protection="MCB", load="6000VA", type="lite", phases=1, desc="Iluminación 1φ")
        .add_circuit(tag="EMG", protection="MCB", load="1200W", type="lite", phases=1, desc="Emergencia")
        .build("Schneider Electric")
    )




