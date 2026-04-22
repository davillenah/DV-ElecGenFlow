from __future__ import annotations

import pytest

from elecgenflow.ingest.errors import MissingTagError
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.registry_bootstrap import ENTRYPOINT_TAG, bootstrap_registry


def test_network_compiler_raises_on_missing_tag() -> None:
    boards = {
        "CCM 48": {"name": "CCM 48", "buses": []},  # ensamble o placeholder
        "TS-FUERZA": {"name": "TS-FUERZA", "main_protection": {"kind": "MCCB"}, "buses": []},
    }

    reg = bootstrap_registry(boards, assemblies=[], network_links=[])

    links = [
        {
            "origin": {"board": "CCM 48", "protection": "Q59"},
            "destination": {"board": "TS-FUERZA", "protection": ENTRYPOINT_TAG},
            "wire": "W123",
            "meta": {},
        }
    ]

    with pytest.raises(MissingTagError):
        compile_network(links, reg)
