# src/elecgenflow/ingest/payload_models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict


class BoardSnapshot(TypedDict, total=False):
    # snapshot generado por electro_core.Board.build()
    name: str
    system: str
    voltage: str
    freq: int
    grounding: str

    main_protection: dict[str, Any]
    leakage_protection: dict[str, Any]
    buses: list[dict[str, Any]]
    standards: list[str]
    meta: dict[str, Any]
    catalog: Any

    # opcional (EPIC-04.00 SSoT)
    endpoints: list[dict[str, Any]]


class EndpointSnapshot(TypedDict, total=False):
    """
    total=False => todas las keys son opcionales salvo las que el caller asegure.
    En nuestro caso, board es conceptualmente obligatorio, pero lo validamos en runtime.
    """

    board: str
    column: str | None
    protection: str | None
    terminal: str | None


class NetworkLinkSnapshot(TypedDict, total=False):
    origin: EndpointSnapshot
    destination: EndpointSnapshot
    wire: str
    meta: dict[str, Any]


class AssemblyColumnSnapshot(TypedDict, total=False):
    index: int
    board: str  # board tag que vive en Plant/Boards


class AssemblySnapshot(TypedDict, total=False):
    name: str
    kind: str  # "CCM" | "TGBT" | etc
    columns: list[AssemblyColumnSnapshot]
    meta: dict[str, Any]


@dataclass(frozen=True)
class ProjectSnapshots:
    boards_by_name: dict[str, BoardSnapshot]
    assemblies: list[AssemblySnapshot]
    network_links: list[NetworkLinkSnapshot]
    owner: dict[str, Any]
