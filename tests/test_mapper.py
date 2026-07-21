from pathlib import Path

from m516.compliance.ingest import ingest_pack
from m516.compliance.mapper import UNMAPPED, map_finding
from m516.compliance.pack_loader import load_pack
from m516.findings import Finding
from m516.models import Asset, Service

STUB_PACK = Path(__file__).parent / "fixtures" / "packs" / "test-stub"


def _admin_panel_finding() -> Finding:
    return Finding(
        asset=Asset(ip="1.2.3.4"),
        service=Service(port=2083, protocol="tcp", product="cpanel"),
        cve_ids=["CVE-TEST-0001"],
        cvss=9.0,
        contextual_score=100,
        severity="critical",
        explanation="An exposed hosting control panel (cPanel) was found directly reachable from the internet.",
        match_confidence="broad",
    )


def test_map_finding_without_llm_client_returns_unmapped_status(tmp_path):
    pack = load_pack(STUB_PACK)
    collection = ingest_pack(pack, chroma_path=str(tmp_path / "chroma"))

    mappings = map_finding(_admin_panel_finding(), pack, collection, llm_client=None, top_k=1)

    assert len(mappings) == 1
    assert mappings[0].clause == "ACME-STD 1.1"
    assert mappings[0].framework == "ACME-STD"
    assert mappings[0].status == UNMAPPED
    assert mappings[0].remediation is None


class _FakeLLMClient:
    def classify(self, finding, clause_title, clause_summary):
        return "non-compliant", f"Restrict access to {clause_title}"


def test_map_finding_with_llm_client_fills_status_and_remediation(tmp_path):
    pack = load_pack(STUB_PACK)
    collection = ingest_pack(pack, chroma_path=str(tmp_path / "chroma"))

    mappings = map_finding(_admin_panel_finding(), pack, collection, llm_client=_FakeLLMClient(), top_k=1)

    assert len(mappings) == 1
    assert mappings[0].status == "non-compliant"
    assert mappings[0].remediation == "Restrict access to No exposed administrative interfaces"
