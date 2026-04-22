# MyProject/Plant/network/electrical_network.py
def build_network_snapshot():
    return [
        # TGBT -> TS-FUERZA (desde ensamble + columna + protección Q59)
        {
            "origin": {"board": "TGBT-GENERAL", "column": "COL-03", "protection": "Q59"},
            "destination": {"board": "TS-FUERZA", "protection": "IG"},
            "wire": "W-TGBT-TSF-4x240",
            "meta": {"desc": "Alimentación TS Fuerza desde TGBT"},
        },
        # TGBT -> TS-CRITICOS
        {
            "origin": {"board": "TGBT-GENERAL", "column": "COL-03", "protection": "Q60"},
            "destination": {"board": "TS-CRITICOS", "protection": "IG"},
            "wire": "W-TGBT-TSC-4x120",
            "meta": {"desc": "Alimentación TS Críticos desde TGBT"},
        },
        # TG-PLANTA -> TGBT (por endpoint del board TG-PLANTA)
        # Acá mostramos que un board normal puede ser fuente usando su endpoint (circuit tag)
        {
            "origin": {"board": "TG-PLANTA", "protection": "dos"},
            "destination": {"board": "TS-CRITICOS", "protection": "IG"},
            "wire": "W-TGPL-TSC-4x25",
            "meta": {"desc": "Ejemplo: origen desde endpoint 'dos' (iluminación oficinas)"},
        },
        # TG-PLANTA -> TS-FUERZA usando subcircuit endpoint
        {
            "origin": {"board": "TG-PLANTA", "protection": "tres:C3"},
            "destination": {"board": "TS-FUERZA", "protection": "IG"},
            "wire": "W-TGPL-TSF-4x16",
            "meta": {"desc": "Ejemplo: origen desde subcircuit endpoint 'tres:C3' (AA split)"},
        },
    ]