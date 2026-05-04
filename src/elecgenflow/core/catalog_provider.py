# src/elecgenflow/core/catalog_provider.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from elecgenflow.core.config import EngineConfig
from elecgenflow.engineering.catalog.ampacity_aea_catalog import AmpacityAEACatalog
from elecgenflow.engineering.catalog.composite_catalog import CompositeCatalog
from elecgenflow.engineering.catalog.derating_catalog import DeratingCatalog
from elecgenflow.engineering.catalog.impedance_catalog import StandardImpedanceCatalog


@dataclass(frozen=True)
class CatalogPaths:
    ampacity_json: str
    derating_json: str

    @staticmethod
    def from_config(cfg: EngineConfig) -> CatalogPaths:
        root = Path(cfg.sizing.nominal_tables_root)
        ver = Path(cfg.sizing.nominal_tables_version)

        amp = root / ver / cfg.sizing.ampacity_filename
        der = root / ver / cfg.sizing.derating_filename

        return CatalogPaths(
            ampacity_json=str(amp.as_posix()),
            derating_json=str(der.as_posix()),
        )


class CatalogProvider:
    """
    Punto único de construcción del catálogo.
    El Core lo llama una vez, y luego el Engine lo usa internamente.
    """

    def __init__(self, *, paths: CatalogPaths, frequency_hz: float = 50.0):
        self.paths = paths
        self.frequency_hz = frequency_hz

    @classmethod
    def from_engine_config(cls, cfg: EngineConfig) -> CatalogProvider:
        paths = CatalogPaths.from_config(cfg)
        return cls(paths=paths, frequency_hz=float(cfg.frequency_hz))

    def build(self) -> CompositeCatalog:
        amp = AmpacityAEACatalog.from_json(self.paths.ampacity_json)
        der = DeratingCatalog.from_json(self.paths.derating_json)
        imp = StandardImpedanceCatalog(default_x_ohm_km=0.08)
        return CompositeCatalog(
            ampacity=amp,
            impedance=imp,
            derating=der,
            frequency_hz=self.frequency_hz,
        )
