# MyProject/Plant/Boards/ts_spare_fuera_servicio.py
from electro_core import Board, MCCB

def build():
    return (
        Board.create("TS-SPARE")
        .configured_as("TRIFASICO", voltage="380/220V", freq=50)
        .grounding_system("TT")
        .main_protection(MCCB(poles=4, amps=125, kA=25))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=160, slots=4)
            .add_circuit(tag="reserva", type="generic", load="0kVA", desc="Reserva", protection="MCB")
        .build("Schneider Electric")
    )