import time
from pathlib import Path

from fastapi.testclient import TestClient

import m516.findings as findings_module
import m516.pipeline as pipeline_module
from m516.api.app import create_app
from m516.enrichment.nvd import CVEMatch
from m516.models import Asset, DiscoveryResult, Service

FIXTURES_PACKS_ROOT = Path(__file__).parent / "fixtures" / "packs"
_CPE = "cpe:2.3:a:x:x:1.0:*:*:*:*:*:*:*"


def _fake_discovery(domain):
    asset = Asset(
        ip="1.2.3.4",
        hostname=domain,
        country="ZZ",
        services=[Service(port=2083, protocol="tcp", product="cpanel", cpe=_CPE)],
    )
    return DiscoveryResult(domain=domain, assets=[asset])


def _fake_lookup(service, api_key, ttl):
    return [
        CVEMatch(
            id="CVE-TEST-0001",
            cvss_score=9.0,
            cvss_severity="CRITICAL",
            published=None,
            description=None,
            match_confidence="broad",
            exploitability_score=None,
            impact_score=None,
        )
    ]


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("PACKS_ROOT", str(FIXTURES_PACKS_ROOT))
    monkeypatch.setenv("DEFAULT_PACK_ID", "test-stub")
    monkeypatch.setenv("REPORT_OUTPUT_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr(pipeline_module, "run_discovery", _fake_discovery)
    monkeypatch.setattr(findings_module, "lookup_cves", _fake_lookup)
    return TestClient(create_app())


def _wait_for_terminal_status(client: TestClient, scan_id: str, attempts: int = 40) -> dict:
    for _ in range(attempts):
        body = client.get(f"/api/scans/{scan_id}").json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.05)
    raise AssertionError("scan did not reach a terminal status in time")


def test_health_endpoint_needs_no_config():
    client = TestClient(create_app())

    assert client.get("/api/health").json() == {"status": "ok"}


def test_list_packs_discovers_the_fixture_packs_root(monkeypatch):
    monkeypatch.setenv("PACKS_ROOT", str(FIXTURES_PACKS_ROOT))
    client = TestClient(create_app())

    resp = client.get("/api/packs")

    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert ids == ["test-stub"]


def test_get_unknown_scan_id_returns_404():
    client = TestClient(create_app())

    resp = client.get("/api/scans/does-not-exist")

    assert resp.status_code == 404


def test_create_scan_without_pack_id_or_default_returns_400(monkeypatch):
    monkeypatch.delenv("DEFAULT_PACK_ID", raising=False)
    client = TestClient(create_app())

    resp = client.post("/api/scans", json={"domain": "example.com"})

    assert resp.status_code == 400


def test_create_scan_with_unknown_pack_id_returns_400(monkeypatch):
    monkeypatch.setenv("PACKS_ROOT", str(FIXTURES_PACKS_ROOT))
    client = TestClient(create_app())

    resp = client.post("/api/scans", json={"domain": "example.com", "pack_id": "does-not-exist"})

    assert resp.status_code == 400


def test_scan_lifecycle_end_to_end(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    create_resp = client.post("/api/scans", json={"domain": "example.com"})
    assert create_resp.status_code == 202
    scan_id = create_resp.json()["scan_id"]

    status = _wait_for_terminal_status(client, scan_id)
    assert status["status"] == "done", status

    dashboard = client.get(f"/api/scans/{scan_id}/dashboard").json()
    assert dashboard["domain"] == "example.com"
    assert dashboard["finding_count"] == 1
    assert dashboard["severity_counts"]["critical"] == 1

    assets = client.get(f"/api/scans/{scan_id}/assets").json()
    assert len(assets) == 1
    assert assets[0]["ip"] == "1.2.3.4"

    findings = client.get(f"/api/scans/{scan_id}/findings").json()
    assert len(findings) == 1
    assert findings[0]["cve_ids"] == ["CVE-TEST-0001"]
    assert findings[0]["service"]["port"] == 2083

    compliance = client.get(f"/api/scans/{scan_id}/compliance").json()
    # mapper.map_finding()'s default top_k=3 candidate clauses for the one finding
    assert len(compliance) == 3
    assert all(gap["status"] == "unmapped" for gap in compliance)  # honest — no llm_client wired (BR-5)

    pdf_resp = client.get(f"/api/scans/{scan_id}/report.pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content[:4] == b"%PDF"


def test_data_endpoints_409_before_scan_is_done(tmp_path, monkeypatch):
    monkeypatch.setenv("PACKS_ROOT", str(FIXTURES_PACKS_ROOT))
    monkeypatch.setenv("DEFAULT_PACK_ID", "test-stub")
    monkeypatch.setenv("REPORT_OUTPUT_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    client = TestClient(create_app())

    # No background task ever runs here (no request submitted), so the state stays "pending" forever —
    # exercises the "not ready yet" branch directly instead of racing the real pipeline.
    import m516.api.state as state_module

    state_module.create("pending-scan", "example.com", "test-stub")

    resp = client.get("/api/scans/pending-scan/dashboard")

    assert resp.status_code == 409
