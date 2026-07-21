"""Compliance pack loader (docs/03_DOMAIN_MODEL.md §2, docs/21_COMPLIANCE_PACKS.md).

A pack is a self-contained unit of sector/country knowledge. The engine knows only this interface — it
never knows "Nigeria" or "CBN" (golden rule). Loading fails loudly on a malformed pack rather than
silently defaulting missing fields; a compliance product cannot afford to guess at regulatory metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


class PackLoadError(Exception):
    """A pack directory is missing, malformed, or missing a required field."""


@dataclass
class Clause:
    ref: str
    title: str
    summary: str
    finding_hints: list[str] = field(default_factory=list)


@dataclass
class Framework:
    id: str
    display_name: str
    issuing_body: str
    documents: list[str]
    clauses: list[Clause] = field(default_factory=list)


@dataclass
class CompliancePack:
    id: str
    display_name: str
    home_country: str
    sector: str
    frameworks: list[Framework]
    report_labels: dict
    path: Path


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise PackLoadError(f"missing required file: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise PackLoadError(f"{path} did not parse to a YAML mapping")
    return data


def _require(data: dict, key: str, context: str) -> object:
    if key not in data or data[key] in (None, ""):
        raise PackLoadError(f"{context} is missing required field '{key}'")
    return data[key]


def _load_framework(pack_dir: Path, framework_id: str) -> Framework:
    fw_path = pack_dir / "frameworks" / f"{framework_id}.yaml"
    data = _read_yaml(fw_path)

    clauses = []
    for i, raw_clause in enumerate(data.get("clauses") or []):
        clause_ctx = f"{fw_path} clause #{i}"
        clauses.append(
            Clause(
                ref=str(_require(raw_clause, "ref", clause_ctx)),
                title=str(_require(raw_clause, "title", clause_ctx)),
                summary=str(_require(raw_clause, "summary", clause_ctx)),
                finding_hints=list(raw_clause.get("finding_hints") or []),
            )
        )

    return Framework(
        id=str(_require(data, "id", str(fw_path))),
        display_name=str(_require(data, "display_name", str(fw_path))),
        issuing_body=str(_require(data, "issuing_body", str(fw_path))),
        documents=list(_require(data, "documents", str(fw_path))),
        clauses=clauses,
    )


def load_pack(pack_dir: Path) -> CompliancePack:
    """Load `pack.yaml` + every referenced `frameworks/<id>.yaml` into a CompliancePack."""
    pack_dir = Path(pack_dir)
    pack_data = _read_yaml(pack_dir / "pack.yaml")

    framework_ids = _require(pack_data, "frameworks", str(pack_dir / "pack.yaml"))
    frameworks = [_load_framework(pack_dir, fw_id) for fw_id in framework_ids]

    return CompliancePack(
        id=str(_require(pack_data, "id", "pack.yaml")),
        display_name=str(_require(pack_data, "display_name", "pack.yaml")),
        home_country=str(_require(pack_data, "home_country", "pack.yaml")),
        sector=str(_require(pack_data, "sector", "pack.yaml")),
        frameworks=frameworks,
        report_labels=dict(pack_data.get("report_labels") or {}),
        path=pack_dir,
    )
