"""HTTP endpoints (docs/05_API_DESIGN.md). Orchestration only — every handler is a thin wrapper over
`m516/pipeline.py` + `m516/api/state.py`; no business logic lives here (docs/07_BACKEND_ARCHITECTURE.md
§1 layering).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from m516.api import state
from m516.api.schemas import (
    AssetSummaryOut,
    ComplianceGapOut,
    FindingOut,
    PackOut,
    ScanCreateRequest,
    ScanStatusOut,
    ScanSummaryOut,
)
from m516.compliance.pack_loader import PackLoadError, load_pack
from m516.config import Config, load_config
from m516.logging import get_logger
from m516.pipeline import run_scan

logger = get_logger(__name__)

router = APIRouter()


def _resolve_pack_id(config: Config, requested: str | None) -> str:
    pack_id = requested or config.default_pack_id
    if not pack_id:
        raise HTTPException(400, "pack_id was not given and no DEFAULT_PACK_ID is configured")
    return pack_id


def _pack_dir(config: Config, pack_id: str) -> Path:
    pack_dir = Path(config.packs_root) / pack_id
    if not (pack_dir / "pack.yaml").exists():
        raise HTTPException(400, f"unknown pack_id '{pack_id}' (no pack.yaml under {pack_dir})")
    return pack_dir


def _require_done(scan_id: str) -> state.ScanState:
    scan_state = state.get(scan_id)
    if scan_state is None:
        raise HTTPException(404, "unknown scan_id")
    if scan_state.status == "error":
        raise HTTPException(409, f"scan failed: {scan_state.error}")
    if scan_state.status != "done":
        raise HTTPException(409, f"scan not finished (status={scan_state.status}, stage={scan_state.stage})")
    return scan_state


def _execute_scan(scan_id: str, domain: str, pack_dir: Path, output_dir: Path, chroma_path: str) -> None:
    state.update(scan_id, status="running")

    try:
        result = run_scan(
            domain,
            pack_dir,
            output_dir,
            scan_id,
            on_stage=lambda stage: state.update(scan_id, stage=stage),
            chroma_path=chroma_path,
        )
    except Exception as exc:  # noqa: BLE001 — a failed scan must not crash the process (NFR-REL)
        logger.exception("scan %s failed", scan_id)
        state.update(scan_id, status="error", error=str(exc), finished_at=datetime.now(timezone.utc))
        return

    state.update(scan_id, status="done", result=result, finished_at=datetime.now(timezone.utc))


@router.post("/scans", status_code=202, response_model=ScanStatusOut)
def create_scan(request: ScanCreateRequest, background_tasks: BackgroundTasks) -> ScanStatusOut:
    config = load_config()
    pack_id = _resolve_pack_id(config, request.pack_id)
    pack_dir = _pack_dir(config, pack_id)

    scan_id = uuid.uuid4().hex
    scan_state = state.create(scan_id, request.domain, pack_id)
    background_tasks.add_task(
        _execute_scan, scan_id, request.domain, pack_dir, Path(config.report_output_dir), config.chroma_path
    )
    return ScanStatusOut.from_state(scan_state)


@router.get("/scans/{scan_id}", response_model=ScanStatusOut)
def get_scan(scan_id: str) -> ScanStatusOut:
    scan_state = state.get(scan_id)
    if scan_state is None:
        raise HTTPException(404, "unknown scan_id")
    return ScanStatusOut.from_state(scan_state)


@router.get("/scans/{scan_id}/dashboard", response_model=ScanSummaryOut)
def get_dashboard(scan_id: str) -> ScanSummaryOut:
    scan_state = _require_done(scan_id)
    return ScanSummaryOut.from_report_data(scan_state.result.report_data)


@router.get("/scans/{scan_id}/assets", response_model=list[AssetSummaryOut])
def get_assets(scan_id: str) -> list[AssetSummaryOut]:
    scan_state = _require_done(scan_id)
    return [AssetSummaryOut.from_asset_summary(a) for a in scan_state.result.report_data.assets]


@router.get("/scans/{scan_id}/findings", response_model=list[FindingOut])
def get_findings(scan_id: str) -> list[FindingOut]:
    scan_state = _require_done(scan_id)
    return [FindingOut.from_finding(f) for f in scan_state.result.findings]


@router.get("/scans/{scan_id}/compliance", response_model=list[ComplianceGapOut])
def get_compliance(scan_id: str) -> list[ComplianceGapOut]:
    scan_state = _require_done(scan_id)
    return [ComplianceGapOut.from_gap(g) for g in scan_state.result.report_data.compliance_gaps]


@router.get("/scans/{scan_id}/report.pdf")
def get_report_pdf(scan_id: str) -> FileResponse:
    scan_state = _require_done(scan_id)
    return FileResponse(scan_state.result.pdf_path, media_type="application/pdf", filename=f"{scan_id}.pdf")


@router.get("/packs", response_model=list[PackOut])
def list_packs() -> list[PackOut]:
    config = load_config()
    root = Path(config.packs_root)
    packs: list[PackOut] = []
    if not root.exists():
        return packs

    for entry in sorted(root.iterdir()):
        if not (entry / "pack.yaml").exists():
            continue
        try:
            packs.append(PackOut.from_pack(load_pack(entry)))
        except PackLoadError:
            logger.warning("skipping malformed pack at %s", entry)
            continue
    return packs


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
