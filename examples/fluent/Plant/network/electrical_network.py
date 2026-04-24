from __future__ import annotations

from electro_core.network import Network


def build(netw: Network) -> Network:
    (
        netw.supply_from("TGBT-GENERAL")
            .column("COL-03")
            .protection("Q59")
            .to("TS-FUERZA")
            .protection("IG")
            .with_wire("W-TGBT-TSF-4x240")
            .done()
    )

    (
        netw.supply_from("TGBT-GENERAL")
            .column("COL-03")
            .protection("Q60")
            .to("TS-CRITICOS")
            .protection("IG")
            .with_wire("W-TGBT-TSC-4x120")
            .done()
    )

    return netw
    '''
    (
        netw.from_source("CCM 48")
            .column("COL-05")
            .protection("QM12")
            .with_wire("4x10mm2")
            .ends_at_load("MOTOR-BOMBA-01")
    )
    '''