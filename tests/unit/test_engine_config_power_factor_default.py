from __future__ import annotations

from pathlib import Path

from elecgenflow.core.config import load_config


def test_power_factor_default_loads_from_yaml(tmp_path: Path) -> None:
    p = tmp_path / "cfg.yaml"
    p.write_text(
        "\n".join(
            [
                "country: AR",
                "frequency_hz: 50",
                "voltages:",
                "  lv: [380, 220]",
                "  mv: [13200, 33000]",
                "standards:",
                "  aea_90364: true",
                "  aea_95403: true",
                "  iec_backup: true",
                "default_seed: 12345",
                "deterministic: true",
                "artifacts_subdir: artifacts",
                "power_factor_default: 0.90",
                "",
            ]
        ),
        encoding="utf-8",
    )

    cfg = load_config(p)
    assert cfg.power_factor_default == 0.90
