# MyProject/Plant/Boards/ts_criticos.py
from electro_core import Board, MCCB

def build():
    return (
        Board.create("TS-CRITICOS")
        .configured_as("TRIFASICO", voltage="380/220V", freq=50)
        .grounding_system("TT")
        .main_protection(MCCB(poles=4, amps=160, kA=25))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=250, slots=6)
            .add_circuit(tag="ups", type="generic", load="8kVA", desc="UPS IT", protection="MCB")
            .add_circuit(tag="seguridad", type="lite", load="3kVA", desc="Iluminación seguridad", protection="MCB")
        .build("Schneider Electric")
    )