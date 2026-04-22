# MyProject/Plant/Boards/tgbt_col_03_salidas.py
from electro_core import Board, MCCB

def build():
    return (
        Board.create("TGBT-COL-03")
        .configured_as("TRIFASICO", voltage="380/220V", freq=50)
        .grounding_system("TT")
        .main_protection(MCCB(poles=4, amps=630, kA=50))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=630, slots=6)
            .add_circuit(tag="Q59", type="generic", desc="Salida a TS-FUERZA", protection="MCCB")
            .add_circuit(tag="Q60", type="generic", desc="Salida a TS-CRITICOS", protection="MCCB")
        .build("Schneider Electric")
    )