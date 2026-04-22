# MyProject/Plant/Boards/tg_planta.py
from electro_core import Board, MCCB, RCCB

def build():
    return (
        Board.create("TG-PLANTA")
        .configured_as("TRIFASICO", voltage="380/220V", freq=50)
        .grounding_system("TT")
        .main_protection(MCCB(poles=4, amps=400, kA=50))
        .leakage_protection(RCCB(type="A", sensitivity="300mA", selective=True))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=630, slots=12)
            .add_circuit(tag="uno", type="lite", load="10kVA", desc="Iluminación nave", protection="MCB")
            .add_circuit(tag="dos", type="lite", load="15kVA", desc="Iluminación oficinas", protection="MCB")
            .add_circuit(tag="tres", type="hvac", desc="HVAC oficinas", protection="RCCB")  # grupo
                .add_sub_circuit(tag="C1", load="2kVA", protection="MCB", desc="Tomas 1")
                .add_sub_circuit(tag="C2", load="2kVA", protection="MCB", desc="Tomas 2")
                .add_sub_circuit(tag="C3", load="3kVA", protection="MCB", desc="AA Split")
                .add_sub_circuit(tag="C4", load="1kVA", protection="MCB", desc="Rack IT")
            .equipped_reserve(device="MCB", qty=4)
        .complying_with(["AEA", "IRAM", "IEC-61439"])
        .build("Schneider Electric")
    )