from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AssemblyKind = Literal["CCM", "TGBT"]


@dataclass(frozen=True)
class CatalogConfig:
    """
    Configuración global de catálogo/materiales para el ensamble.
    En EPIC-04.00 esto se trata como metadata (no selección automática).
    """

    switchgear: str | None = None
    enclosure: str | None = None
    busbar_material: str | None = None
    cable: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class MainBusbarSpec:
    capacity: int
    coating: str = "NATURAL"
    segregation: str = "2b"
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ColumnSpec:
    """
    Columna física del ensamble.
    - index: 1..N (se traduce luego a COL-01..COL-NN en el bootstrap del Registry)
    - board: tag del board (nombre del tablero) que vive en Plant/Boards
    """

    index: int
    board: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssemblySnapshot:
    """
    Snapshot serializable del ensamble.
    Esto es lo que board_assembly.py debe devolver al motor (lista de dicts).
    """

    name: str
    kind: AssemblyKind = "CCM"
    catalog: CatalogConfig | None = None
    main_busbar: MainBusbarSpec | None = None

    layout: dict[str, Any] = field(default_factory=dict)
    dimensions: dict[str, Any] = field(default_factory=dict)

    columns: list[ColumnSpec] = field(default_factory=list)

    service_state: Literal["in_service", "out_of_service"] = "in_service"
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssemblyArtifact:
    """
    Resultado de .build() para permitir:
        .build().in_service()
        .build().out_of_service()

    Devuelve dict snapshot listo para el project_loader.
    """

    snapshot: AssemblySnapshot

    def in_service(self) -> dict[str, Any]:
        snap = self._clone(service_state="in_service")
        return asdict(snap)

    def out_of_service(self) -> dict[str, Any]:
        snap = self._clone(service_state="out_of_service")
        return asdict(snap)

    def to_dict(self) -> dict[str, Any]:
        # por defecto, lo que se construye queda in_service
        return asdict(self.snapshot)

    def _clone(self, *, service_state: str) -> AssemblySnapshot:
        s = self.snapshot
        return AssemblySnapshot(
            name=s.name,
            kind=s.kind,
            catalog=s.catalog,
            main_busbar=s.main_busbar,
            layout=dict(s.layout),
            dimensions=dict(s.dimensions),
            columns=list(s.columns),
            service_state=service_state,  # type: ignore[arg-type]
            meta=dict(s.meta),
        )


def _board_tag(board: str | dict[str, Any] | Any) -> str:
    """
    Acepta:
      - "TS-FUERZA" (string)
      - snapshot dict devuelto por Board.build() con key 'name'
      - cualquier objeto con atributo .get('name') o .name
    Devuelve el tag del tablero.
    """
    if isinstance(board, str):
        return board

    if isinstance(board, dict):
        name = board.get("name")
        if isinstance(name, str) and name:
            return name
        raise ValueError("Column board snapshot dict debe incluir key 'name'")

    # fallback: intenta attribute .name
    name = getattr(board, "name", None)
    if isinstance(name, str) and name:
        return name

    raise ValueError("board debe ser str (tag) o snapshot dict con 'name'")


class AssemblyBuilder:
    """
    DSL para construir ensambles de tableros (CCM/TGBT/etc).

    Uso:
      CCM.assembly("CCM 48")
        .built_with(...)
        .main_busbar(...)
        .add_column(index=1, board=columna_1.build())
        ...
        .layout(arrangement="IN_LINE")
        .total_dimensions(height=2200, depth=800)
        .build()
        .in_service()
    """

    def __init__(self, name: str, kind: AssemblyKind):
        self._snap = AssemblySnapshot(name=name, kind=kind)

    def built_with(
        self,
        *,
        switchgear: str | None = None,
        enclosure: str | None = None,
        busbar_material: str | None = None,
        cable: str | None = None,
        **meta: Any,
    ) -> AssemblyBuilder:
        self._snap.catalog = CatalogConfig(
            switchgear=switchgear,
            enclosure=enclosure,
            busbar_material=busbar_material,
            cable=cable,
            meta=dict(meta),
        )
        return self

    def with_global_config(self, config: CatalogConfig) -> AssemblyBuilder:
        self._snap.catalog = config
        return self

    def main_busbar(
        self,
        *,
        capacity: int,
        coating: str = "NATURAL",
        segregation: str = "2b",
        **meta: Any,
    ) -> AssemblyBuilder:
        self._snap.main_busbar = MainBusbarSpec(
            capacity=int(capacity),
            coating=str(coating),
            segregation=str(segregation),
            meta=dict(meta),
        )
        return self

    def add_column(
        self,
        *,
        index: int,
        board: str | dict[str, Any] | Any,
        **meta: Any,
    ) -> AssemblyBuilder:
        btag = _board_tag(board)
        self._snap.columns.append(ColumnSpec(index=int(index), board=btag, meta=dict(meta)))
        return self

    def layout(self, **kwargs: Any) -> AssemblyBuilder:
        self._snap.layout.update(dict(kwargs))
        return self

    def total_dimensions(self, **kwargs: Any) -> AssemblyBuilder:
        self._snap.dimensions.update(dict(kwargs))
        return self

    def meta(self, **kwargs: Any) -> AssemblyBuilder:
        self._snap.meta.update(dict(kwargs))
        return self

    def build(self) -> AssemblyArtifact:
        # build NO devuelve dict directamente para permitir .in_service() / .out_of_service()
        return AssemblyArtifact(snapshot=self._snap)


class CCM:
    @staticmethod
    def assembly(name: str) -> AssemblyBuilder:
        return AssemblyBuilder(name=name, kind="CCM")


class TGBT:
    @staticmethod
    def assembly(name: str) -> AssemblyBuilder:
        return AssemblyBuilder(name=name, kind="TGBT")
