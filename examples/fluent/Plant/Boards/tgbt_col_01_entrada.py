# MyProject/Plant/Boards/tgbt_col_01_entrada.py
from electro_core import Board, MCCB

def build():
    return (
        Board.create("TGBT-COL-01")
        .configured_as("TRIFASICO", voltage="380/220V", freq=50)
        .grounding_system("TT")
        .main_protection(MCCB(poles=4, amps=1000, kA=65))
        .distribution_bus(material="COBRE", coating="PAINTED", capacity=1000, slots=3)
            .add_circuit(tag="Q01", type="generic", desc="Salida principal hacia barras", protection="MCCB")
        .build("Schneider Electric")
    )