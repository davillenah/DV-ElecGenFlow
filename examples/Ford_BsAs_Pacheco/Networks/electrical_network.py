# examples/Ford_BsAs_Pachecho/Networks/electrical_network.py

from __future__ import annotations

from electro_core.network import Network


def build(network: Network) -> Network:
    # Desde TGBT-COL-03 hacia TS-LITE/POWR (usa Q59..Q62 definidos en tgbt_col03.py)
    (
        network.supply_from("TGBT_GENERAL")
        .column("COL-03")
        .protection("Q59")
        .to("TS_LITE_01")
        .protection("IG")
        .with_wire_id("W378")
        .configured_as()
        .multipolar()
        .with_protection_cable_included()
        .insulation("PVC")
        .conductor("AL")
        .installed_in("E")
        .circuits(parallel=1, grouped=1)
        .done()
    )

    (
        network.supply_from("TGBT_GENERAL")
        .column("COL-03")
        .protection("Q60")
        .to("TS_LITE_02")
        .protection("IG")
        .with_wire_id("W379")
        .configured_as()
        .multipolar()
        .without_protection_cable_included()
        .insulation("PVC")
        .conductor("CU")
        .installed_in("B2")
        .circuits(parallel=1, grouped=3)
        .done()
    )

    (
        network.supply_from("TGBT_GENERAL")
        .column("COL-03")
        .protection("Q61")
        .to("TS_POWR_01")
        .protection("IG")
        .with_wire_id("W380")
        .configured_as()
        .unipolar("horizontal")
        .insulation("XLPE")
        .conductor("AL")
        .installed_in("D1")
        .buried_at(depth_m=0.7)
        .circuits(parallel=2, grouped=1)
        .done()
    )

    (
        network.supply_from("TGBT_GENERAL")
        .column("COL-03")
        .protection("Q62")
        .to("TS_POWR_02")
        .protection("IG")
        .with_wire_id("W381")
        .configured_as()
        .unipolar("vertical")
        .insulation("XLPE")
        .conductor("CU")
        .installed_in("D2")
        .buried_at(depth_m=0.7)
        .circuits(parallel=3, grouped=1)
        .done()
    )

    return network




