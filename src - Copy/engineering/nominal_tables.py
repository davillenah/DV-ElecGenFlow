from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, ValidationError


class CableSpec(BaseModel):
    tag: str
    manufacturer: str = "GENERIC"
    family: str
    material: Literal["CU", "AL"]
    insulation: str
    jacket: str | None = None
    cores: int = Field(ge=1, le=12)
    section_mm2: float = Field(gt=0)
    voltage_class: Literal["LV", "MV"] = "LV"
    ampacity_a: float | None = Field(default=None, gt=0)
    resistance_ohm_km_20c: float | None = Field(default=None, gt=0)
    meta: dict[str, Any] = Field(default_factory=dict)


class ProtectionSpec(BaseModel):
    tag: str
    manufacturer: str = "GENERIC"
    kind: Literal["MCB", "MCCB", "RCCB", "FUSE", "ACB"] = "MCCB"
    poles: int = Field(ge=1, le=4)
    rating_amps: int = Field(ge=1)
    breaking_capacity_ka: int | None = Field(default=None, ge=1)
    curve: str | None = None
    trip_unit: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class InstallMethodSpec(BaseModel):
    tag: str
    description: str
    meta: dict[str, Any] = Field(default_factory=dict)


class NominalFile(BaseModel):
    version: str
    kind: Literal["cables", "protections", "install_methods"]
    items: list[dict[str, Any]] = Field(default_factory=list)

    # overlay metadata (optional)
    overlay: bool = False
    manufacturer: str | None = None


class NominalLookupError(Exception):
    def __init__(
        self,
        *,
        kind: str,
        tag: str,
        message: str,
        suggestions: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.tag = tag
        self.suggestions = suggestions or []

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "tag": self.tag,
            "message": str(self),
            "suggestions": self.suggestions,
        }


@dataclass(frozen=True)
class NominalTables:
    version: str
    cables: dict[str, CableSpec]
    protections: dict[str, ProtectionSpec]
    install_methods: dict[str, InstallMethodSpec]
    overlays_applied: list[str]

    def _suggest(self, keys: list[str], tag: str, limit: int = 10) -> list[str]:
        t = tag.lower()
        hits = [k for k in keys if t in k.lower()]
        if hits:
            return hits[:limit]
        # fallback: same prefix before first dash
        prefix = tag.split("-")[0].lower() if "-" in tag else t[:3]
        hits2 = [k for k in keys if k.lower().startswith(prefix)]
        return hits2[:limit]

    def get_cable(self, tag: str) -> CableSpec:
        if tag in self.cables:
            return self.cables[tag]
        suggestions = self._suggest(list(self.cables.keys()), tag)
        raise NominalLookupError(
            kind="cables",
            tag=tag,
            message=f"Cable tag no encontrado: {tag}",
            suggestions=suggestions,
        )

    def get_protection(self, tag: str) -> ProtectionSpec:
        if tag in self.protections:
            return self.protections[tag]
        suggestions = self._suggest(list(self.protections.keys()), tag)
        raise NominalLookupError(
            kind="protections",
            tag=tag,
            message=f"Protection tag no encontrado: {tag}",
            suggestions=suggestions,
        )

    def get_install_method(self, tag: str) -> InstallMethodSpec:
        if tag in self.install_methods:
            return self.install_methods[tag]
        suggestions = self._suggest(list(self.install_methods.keys()), tag)
        raise NominalLookupError(
            kind="install_methods",
            tag=tag,
            message=f"Install method tag no encontrado: {tag}",
            suggestions=suggestions,
        )


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Nominal JSON debe ser un objeto (dict): {path}")
    return cast(dict[str, Any], data)


def _load_nominal_file(path: Path) -> NominalFile:
    data = _read_json(path)
    try:
        return NominalFile.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Nominal JSON inválido: {path}\n{exc}") from exc


def _merge_by_tag(
    base: dict[str, dict[str, Any]], overlay: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    out = dict(base)
    out.update(overlay)  # overlay pisa por tag
    return out


def _to_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for x in items:
        tag = x.get("tag")
        if isinstance(tag, str) and tag:
            out[tag] = x
    return out


def load_nominal_tables(
    *,
    root: Path = Path("data/nominal"),
    version: str = "v0",
    overlays: list[Path] | None = None,
) -> NominalTables:
    overlays = overlays or []
    base_dir = root / version
    if not base_dir.exists():
        raise FileNotFoundError(f"Nominal tables base dir no existe: {base_dir}")

    cables_file = base_dir / "cables.json"
    prot_file = base_dir / "protections.json"
    inst_file = base_dir / "install_methods.json"

    base_cables = _load_nominal_file(cables_file)
    base_prot = _load_nominal_file(prot_file)
    base_inst = _load_nominal_file(inst_file)

    if base_cables.kind != "cables":
        raise ValueError("cables.json kind debe ser 'cables'")
    if base_prot.kind != "protections":
        raise ValueError("protections.json kind debe ser 'protections'")
    if base_inst.kind != "install_methods":
        raise ValueError("install_methods.json kind debe ser 'install_methods'")

    cables_by_tag = _to_map(base_cables.items)
    prot_by_tag = _to_map(base_prot.items)
    inst_by_tag = _to_map(base_inst.items)

    overlays_applied: list[str] = []

    for ov in overlays:
        nf = _load_nominal_file(ov)
        if not nf.overlay:
            raise ValueError(f"Overlay file debe incluir overlay=true: {ov}")

        ov_map = _to_map(nf.items)
        if nf.kind == "cables":
            cables_by_tag = _merge_by_tag(cables_by_tag, ov_map)
        elif nf.kind == "protections":
            prot_by_tag = _merge_by_tag(prot_by_tag, ov_map)
        elif nf.kind == "install_methods":
            inst_by_tag = _merge_by_tag(inst_by_tag, ov_map)
        else:
            raise ValueError(f"kind no soportado en overlay: {nf.kind}")

        overlays_applied.append(str(ov))

    cables: dict[str, CableSpec] = {}
    for tag, d in cables_by_tag.items():
        try:
            cables[tag] = CableSpec.model_validate(d)
        except ValidationError as exc:
            raise ValueError(f"CableSpec inválido tag={tag}\n{exc}") from exc

    protections: dict[str, ProtectionSpec] = {}
    for tag, d in prot_by_tag.items():
        try:
            protections[tag] = ProtectionSpec.model_validate(d)
        except ValidationError as exc:
            raise ValueError(f"ProtectionSpec inválido tag={tag}\n{exc}") from exc

    install_methods: dict[str, InstallMethodSpec] = {}
    for tag, d in inst_by_tag.items():
        try:
            install_methods[tag] = InstallMethodSpec.model_validate(d)
        except ValidationError as exc:
            raise ValueError(f"InstallMethodSpec inválido tag={tag}\n{exc}") from exc

    return NominalTables(
        version=version,
        cables=cables,
        protections=protections,
        install_methods=install_methods,
        overlays_applied=overlays_applied,
    )


def nominal_snapshot(tables: NominalTables) -> dict[str, Any]:
    return {
        "version": tables.version,
        "counts": {
            "cables": len(tables.cables),
            "protections": len(tables.protections),
            "install_methods": len(tables.install_methods),
        },
        "overlays_applied": list(tables.overlays_applied),
        "index": {
            "cables": sorted(tables.cables.keys()),
            "protections": sorted(tables.protections.keys()),
            "install_methods": sorted(tables.install_methods.keys()),
        },
    }


def nominal_snapshot_md(tables: NominalTables) -> str:
    snap = nominal_snapshot(tables)
    lines: list[str] = []
    lines.append("# Nominal Tables Snapshot (EPIC-04.03)")
    lines.append("")
    lines.append(f"**Version:** {snap['version']}")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- cables: {snap['counts']['cables']}")
    lines.append(f"- protections: {snap['counts']['protections']}")
    lines.append(f"- install_methods: {snap['counts']['install_methods']}")
    lines.append("")
    if snap["overlays_applied"]:
        lines.append("## Overlays applied")
        lines.append("")
        for ov in snap["overlays_applied"]:
            lines.append(f"- {ov}")
        lines.append("")
    lines.append("## Index")
    lines.append("")
    lines.append("### Cables")
    for t in snap["index"]["cables"]:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("### Protections")
    for t in snap["index"]["protections"]:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("### Install methods")
    for t in snap["index"]["install_methods"]:
        lines.append(f"- {t}")
    lines.append("")
    return "\n".join(lines)


def _dump_spec_map(m: Mapping[str, BaseModel]) -> dict[str, dict[str, Any]]:
    return {k: v.model_dump(mode="json") for k, v in m.items()}


def nominal_overlay_diff(
    *,
    root: Path,
    version: str,
    overlays: list[Path],
) -> dict[str, Any]:
    """Diff entre base (sin overlays) y merged (con overlays)."""
    base = load_nominal_tables(root=root, version=version, overlays=[])
    merged = load_nominal_tables(root=root, version=version, overlays=overlays)

    base_c = _dump_spec_map(base.cables)
    base_p = _dump_spec_map(base.protections)
    base_i = _dump_spec_map(base.install_methods)

    merged_c = _dump_spec_map(merged.cables)
    merged_p = _dump_spec_map(merged.protections)
    merged_i = _dump_spec_map(merged.install_methods)

    def diff_kind(b: dict[str, dict[str, Any]], m: dict[str, dict[str, Any]]) -> dict[str, Any]:
        changed: dict[str, Any] = {}
        added = sorted([k for k in m if k not in b])
        removed = sorted([k for k in b if k not in m])
        common = [k for k in m if k in b]

        for k in common:
            if b[k] != m[k]:
                changed[k] = {"before": b[k], "after": m[k]}

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
        }

    return {
        "version": version,
        "overlays": [str(p) for p in overlays],
        "cables": diff_kind(base_c, merged_c),
        "protections": diff_kind(base_p, merged_p),
        "install_methods": diff_kind(base_i, merged_i),
    }


def nominal_overlay_diff_md(diff: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Nominal Overlay Diff (EPIC-04.03)")
    lines.append("")
    lines.append(f"**Version:** {diff.get('version')}")
    lines.append("")
    ovs = diff.get("overlays") or []
    lines.append("## Overlays")
    lines.append("")
    if ovs:
        for o in ovs:
            lines.append(f"- {o}")
    else:
        lines.append("- (none)")
    lines.append("")

    def section(name: str, d: dict[str, Any]) -> None:
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- added: {len(d.get('added') or [])}")
        lines.append(f"- removed: {len(d.get('removed') or [])}")
        lines.append(f"- changed: {len((d.get('changed') or {}).keys())}")
        lines.append("")
        if d.get("added"):
            lines.append("### Added")
            for x in d["added"]:
                lines.append(f"- {x}")
            lines.append("")
        if d.get("removed"):
            lines.append("### Removed")
            for x in d["removed"]:
                lines.append(f"- {x}")
            lines.append("")
        if d.get("changed"):
            lines.append("### Changed")
            for k in sorted(d["changed"].keys()):
                lines.append(f"- {k}")
            lines.append("")

    section("Cables", cast(dict[str, Any], diff.get("cables") or {}))
    section("Protections", cast(dict[str, Any], diff.get("protections") or {}))
    section("Install methods", cast(dict[str, Any], diff.get("install_methods") or {}))

    return "\n".join(lines)
