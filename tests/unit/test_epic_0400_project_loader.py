from __future__ import annotations

from pathlib import Path

from elecgenflow.ingest.project_loader import load_project


def test_project_loader_discovers_boards(tmp_path: Path) -> None:
    project = tmp_path / "Project"
    boards_dir = project / "Plant" / "Boards"
    boards_dir.mkdir(parents=True)

    # board file
    (boards_dir / "ts_fuerza.py").write_text(
        "def build():\n"
        "    return {'name': 'TS-FUERZA', 'main_protection': {'kind': 'MCCB'}, 'buses': []}\n",
        encoding="utf-8",
    )

    snapshots = load_project(project)
    assert "TS-FUERZA" in snapshots.boards_by_name
