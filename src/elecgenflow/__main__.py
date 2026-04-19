# src/elecgenflow/__main__.py
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from elecgenflow.core.config import load_config
from elecgenflow.core.engine import Engine
from elecgenflow.domain.contracts.problem import DesignProblem

logger = logging.getLogger(__name__)


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

    try:
        cfg = load_config(Path(args.config))
        engine = Engine(cfg)

        if not args.problem:
            logger.info("No --problem provided. CLI only validates config + contracts.")
            return 0

        problem_path = Path(args.problem)
        problem_json = problem_path.read_text(encoding="utf-8")
        problem = DesignProblem.model_validate_json(problem_json)

        result = engine.run(problem, out_dir=Path(args.out))
        logger.info(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return 0

    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        return 1
    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
