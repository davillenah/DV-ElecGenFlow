from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from elecgenflow import __version__


def _sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RunManifest:
    """Manifest de ejecución para reproducibilidad."""

    engine_version: str
    created_utc: str
    seed: int
    config_sha256: str
    problem_sha256: str
    notes: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(seed: int, config_text: str, problem_text: str, notes: dict[str, Any] | None = None) -> "RunManifest":
        return RunManifest(
            engine_version=__version__,
            created_utc=datetime.now(timezone.utc).isoformat(),
            seed=seed,
            config_sha256=_sha256_text(config_text),
            problem_sha256=_sha256_text(problem_text),
            notes=notes or {},
        )

    def to_json(self) -> str:
        import json
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
