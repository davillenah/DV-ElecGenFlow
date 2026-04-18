from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from pydantic import BaseModel


def export_json_schema(model: Type[BaseModel], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    schema = model.model_json_schema()
    out_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
