# examples/Ford_BsAs_Pachecho/Boards/CCM_Ecoat/ccm_ecoat_col01.py

from __future__ import annotations

from electro_core import Board, MCCB


def build():
    return (
        Board.id("CCM_ECOAT_COL01")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=400, kA=36))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=400, slots=10)
        .add_circuit(tag="M01", protection="MCCB", load="30HP", type="motor", phases=3, desc="Motor ECoat 01")
        .add_circuit(tag="M02", protection="MCCB", load="15HP", type="motor", phases=3, desc="Motor ECoat 02")
        .build("Schneider Electric")
    )