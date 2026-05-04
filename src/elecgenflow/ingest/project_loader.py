# src/elecgenflow/ingest/project_loader.py

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


def _iter_board_files(boards_root: Path) -> list[Path]:
    """
    Devuelve todos los *.py bajo Boards/**, excluyendo *_assembly.py y archivos privados.
    (Soporta estructura nueva recursiva).
    """
    out: list[Path] = []
    for py in sorted(boards_root.glob("**/*.py")):
        if py.name.startswith("_"):
            continue
        if py.name.endswith("_assembly.py"):
            continue
        out.append(py)
    return out


def _load_assemblies_from_module(py: Path) -> list[AssemblySnapshot]:
    """
    Carga un módulo de assembly y devuelve lista de snapshots.
    Acepta:
      - build_assemblies() -> list[dict]
      - ASSEMBLIES = list[dict] (o dict)
    """
    mod = import_module_from_path(f"plant_asm_{py.stem}", py)
    data = call_if_exists(mod, "build_assemblies")
    if data is None:
        data = getattr(mod, "ASSEMBLIES", None)

    if data is None:
        return []
    if isinstance(data, list):
        return cast(list[AssemblySnapshot], data)
    if isinstance(data, dict):
        return [cast(AssemblySnapshot, data)]
    raise ProjectLoadError(f"{py} debe exponer build_assemblies()->list o ASSEMBLIES=list/dict")


def load_project(project_root: Path) -> ProjectSnapshots:
    if not project_root.exists():
        raise ProjectLoadError(f"Project root no existe: {project_root}")

    # -------------------------
    # Soportar 2 estructuras:
    # A) vieja: project_root/Plant/Boards
    # B) nueva: project_root/Boards
    # -------------------------
    plant_dir = project_root / "Plant"
    boards_dir_old = plant_dir / "Boards"
    boards_dir_new = project_root / "Boards"

    if boards_dir_old.exists():
        # Estructura vieja
        boards_dir = boards_dir_old
        networks_dir = plant_dir / "network"
        assemblies_search_roots = [plant_dir]  # busca *_assembly.py en Plant/**
        network_candidates = [
            networks_dir / "electrical_network.py",
            plant_dir / "electrical_network.py",
        ]
    elif boards_dir_new.exists():
        # Estructura nueva
        boards_dir = boards_dir_new
        networks_dir = project_root / "Networks"
        assemblies_search_roots = [boards_dir_new]  # busca *_assembly.py en Boards/**
        network_candidates = [
            networks_dir / "electrical_network.py",
            networks_dir / "electrocal_network.py",
        ]
    else:
        raise ProjectLoadError(f"Falta Boards: {boards_dir_old} o {boards_dir_new}")

    # -------------------------
    # Boards (recursivo en estructura nueva)
    # -------------------------
    boards_by_name: dict[str, BoardSnapshot] = {}
    for py in _iter_board_files(boards_dir):
        # nombre de módulo estable y único
        mod = import_module_from_path(f"board_{py.parent.name}_{py.stem}", py)
        board_snapshot_any = call_if_exists(mod, "build")
        if not isinstance(board_snapshot_any, dict):
            raise ProjectLoadError(
                f"{py} build() debe devolver dict, got={type(board_snapshot_any)}"
            )
        name = board_snapshot_any.get("name") or py.stem
        boards_by_name[str(name)] = cast(BoardSnapshot, board_snapshot_any)

    # -------------------------
    # Assemblies (estructura vieja o nueva)
    # - vieja: típicamente Plant/ccm_assembly.py
    # - nueva: *_assembly.py dentro de Boards/**
    # -------------------------
    assemblies: list[AssemblySnapshot] = []

    # Caso viejo explícito: Plant/ccm_assembly.py (si existe)
    legacy_asm = plant_dir / "ccm_assembly.py"
    if legacy_asm.exists():
        assemblies.extend(_load_assemblies_from_module(legacy_asm))

    # Caso general: buscar *_assembly.py bajo los roots seleccionados
    for root in assemblies_search_roots:
        for asm_py in sorted(root.glob("**/*_assembly.py")):
            # evitamos duplicar si ya cargamos legacy_asm
            if asm_py.resolve() == legacy_asm.resolve():
                continue
            assemblies.extend(_load_assemblies_from_module(asm_py))

    # -------------------------
    # Network
    # - vieja: Plant/network/electrical_network.py o Plant/electrical_network.py
    # - nueva: Networks/electrical_network.py o primer *network.py
    # -------------------------
    network_links: list[NetworkLinkSnapshot] = []
    network_file: str | None = None

    net_file = _find_first_existing(network_candidates)

    # fallback (estructura nueva): primer *_network.py dentro de Networks/
    if net_file is None and networks_dir.exists():
        cand = sorted(networks_dir.glob("*network.py"))
        net_file = cand[0] if cand else None

    if net_file is not None:
        network_file = str(net_file)
        net_mod = import_module_from_path("plant_network", net_file)
        data = call_if_exists(net_mod, "build_network_snapshot")
        network_links = cast(list[NetworkLinkSnapshot], data) if isinstance(data, list) else []

    # -------------------------
    # Owner
    # -------------------------
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
