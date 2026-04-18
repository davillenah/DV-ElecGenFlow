from __future__ import annotations

import argparse
import json
from pathlib import Path

from elecgenflow.core.config import load_config
from elecgenflow.core.engine import Engine
from elecgenflow.domain.contracts.problem import DesignProblem


def main() -> int:
    parser = argparse.ArgumentParser(prog="elecgenflow", description="elecgenflow headless engine")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/default_ar.yaml",
        help="Path to engine config YAML (default: configs/default_ar.yaml)",
    )
    parser.add_argument("--problem", type=str, help="Path to DesignProblem JSON file")
    parser.add_argument("--out", type=str, default="out", help="Output folder for artifacts")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    engine = Engine(cfg)

    if not args.problem:
        print("No --problem provided. (EPIC-1) CLI only validates config + contracts.")
        return 0

    problem_json = Path(args.problem).read_text(encoding="utf-8")
    problem = DesignProblem.model_validate_json(problem_json)

    result = engine.run(problem, out_dir=Path(args.out))
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
