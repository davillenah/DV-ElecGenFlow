from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict


class BoardSnapshot(TypedDict, total=False):
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

    endpoints: list[dict[str, Any]]


class EndpointSnapshot(TypedDict, total=False):
    board: str
    column: str | None
    protection: str | None
    terminal: str | None
    load: str | None  # destino final (carga virtual)


class NetworkLinkSnapshot(TypedDict, total=False):
    origin: EndpointSnapshot
    destination: EndpointSnapshot
    wire: str
    meta: dict[str, Any]


class AssemblyColumnSnapshot(TypedDict, total=False):
    index: int
    board: str


class AssemblySnapshot(TypedDict, total=False):
    name: str
    kind: str
    columns: list[AssemblyColumnSnapshot]
    meta: dict[str, Any]


@dataclass(frozen=True)
class ProjectSnapshots:
    boards_by_name: dict[str, BoardSnapshot]
    assemblies: list[AssemblySnapshot]
    network_links: list[NetworkLinkSnapshot]
    network_file: str | None
    owner: dict[str, Any]
