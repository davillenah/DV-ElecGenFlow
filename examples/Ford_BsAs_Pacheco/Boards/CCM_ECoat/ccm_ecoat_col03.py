# examples/Ford_BsAs_Pachecho/Boards/CCM_Ecoat/ccm_ecoat_col03.py

from __future__ import annotations

from electro_core import Board, MCCB, RCCB


def build():
    return (
        Board.id("CCM_ECOAT_COL03")
        .configured_as(phases=3, voltage="380/220V", freq=50, grounding_system="TT")
        .main_protection(MCCB(poles=4, amps=400, kA=36))
        .leakage_protection(RCCB(type="A", sensitivity_mA=300, selective=True))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=400, slots=12)
        .add_circuit(tag="G1", protection="RCCB", load=None, type="hvac", phases=3, desc="Grupo HVAC ECoat")
        .add_sub_circuit(tag="C1", protection="MCB", load="2kVA", type="lite", phases=1, desc="Tomas")
        .add_sub_circuit(tag="C2", protection="MCB", load="3000W", type="hvac", phases=1, desc="Split")
        .add_sub_circuit(tag="C3", protection="MCB", load="1kW", type="generic", phases=1, desc="Rack")
        .build("Schneider Electric")
    )