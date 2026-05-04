# examples/Ford_BsAs_Pachecho/Boards/CCM_Ecoat/ccm_ecoat_col02.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("CCM_ECOAT_COL02")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=400, kA=36))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=400, slots=10)
        .add_circuit(tag="M03", protection="MCCB", load="22kW", type="motor", phases=3, desc="Motor ECoat 03")
        .add_circuit(tag="AUX", protection="MCB", load="5kVA", type="lite", phases=1, desc="Aux 1φ")
        .build("Schneider Electric")
    )