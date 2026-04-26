from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from .errors import ProjectLoadError
from .import_utils import call_if_exists, import_module_from_path
from .payload_models import AssemblySnapshot, BoardSnapshot, NetworkLinkSnapshot, ProjectSnapshots


def _find_first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def load_project(project_root: Path) -> ProjectSnapshots:
    if not project_root.exists():
        raise ProjectLoadError(f"Project root no existe: {project_root}")

    plant_dir = project_root / "Plant"
    boards_dir = plant_dir / "Boards"
    if not boards_dir.exists():
        raise ProjectLoadError(f"Falta Plant/Boards: {boards_dir}")

    boards_by_name: dict[str, BoardSnapshot] = {}
    for py in sorted(boards_dir.glob("*.py")):
        if py.name.startswith("_"):
            continue
        mod = import_module_from_path(f"plant_board_{py.stem}", py)
        board_snapshot_any = call_if_exists(mod, "build")
        if not isinstance(board_snapshot_any, dict):
            raise ProjectLoadError(
                f"{py} build() debe devolver dict, got={type(board_snapshot_any)}"
            )
        name = board_snapshot_any.get("name") or py.stem
        boards_by_name[str(name)] = cast(BoardSnapshot, board_snapshot_any)

    assemblies: list[AssemblySnapshot] = []
    asm_path = plant_dir / "ccm_assembly.py"
    if asm_path.exists():
        asm_mod = import_module_from_path("plant_ccm_assembly", asm_path)
        data = call_if_exists(asm_mod, "build_assemblies")
        if data is None:
            data = getattr(asm_mod, "ASSEMBLIES", None)

        if data is None:
            assemblies = []
        elif isinstance(data, list):
            assemblies = cast(list[AssemblySnapshot], data)
        elif isinstance(data, dict):
            assemblies = [cast(AssemblySnapshot, data)]
        else:
            raise ProjectLoadError(
                "ccm_assembly.py debe exponer build_assemblies()->list o ASSEMBLIES=list"
            )

    network_links: list[NetworkLinkSnapshot] = []
    network_file: str | None = None

    net_file = _find_first_existing(
        [
            plant_dir / "network" / "electrical_network.py",
            plant_dir / "electrical_network.py",
        ]
    )
    if net_file is not None:
        network_file = str(net_file)
        net_mod = import_module_from_path("plant_network", net_file)

        data = call_if_exists(net_mod, "build_network_snapshot")
        network_links = cast(list[NetworkLinkSnapshot], data) if isinstance(data, list) else []

    owner: dict[str, Any] = {}
    owner_file = project_root / "project_owner.py"
    if owner_file.exists():
        owner_mod = import_module_from_path("project_owner", owner_file)
        data = getattr(owner_mod, "OWNER", None)
        if data is None:
            data = call_if_exists(owner_mod, "build_owner")
        if isinstance(data, dict):
            owner = cast(dict[str, Any], data)

    return ProjectSnapshots(
        boards_by_name=boards_by_name,
        assemblies=assemblies,
        network_links=network_links,
        network_file=network_file,
        owner=owner,
    )
