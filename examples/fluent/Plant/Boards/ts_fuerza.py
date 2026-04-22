# MyProject/Plant/Boards/ts_fuerza.py
from electro_core import Board, MCCB

def build():
    return (
        Board.create("TS-FUERZA")
        .configured_as("TRIFASICO", voltage="380/220V", freq=50)
        .grounding_system("TT")
        .main_protection(MCCB(poles=4, amps=250, kA=36))
        .distribution_bus(material="COBRE", coating="HEAT_SHRINK", capacity=400, slots=8)
            .add_circuit(tag="bombas", type="motor", load="22kW", desc="Bombas principales", protection="MCCB")
            .add_circuit(tag="aire", type="hvac", load="15kW", desc="AA central", protection="MCCB")
        .complying_with(["AEA", "IRAM", "IEC-61439"])
        .build("Schneider Electric")
    )