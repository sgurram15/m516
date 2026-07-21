from pathlib import Path

from m516.compliance.ingest import ingest_pack
from m516.compliance.pack_loader import load_pack
from m516.compliance.retrieve import retrieve_clauses
from m516.findings import Finding
from m516.models import Asset, Service

STUB_PACK = Path(__file__).parent / "fixtures" / "packs" / "test-stub"


def _finding(explanation: str, product: str, port: int) -> Finding:
    asset = Asset(ip="1.2.3.4")
    service = Service(port=port, protocol="tcp", product=product)
    return Finding(
        asset=asset,
        service=service,
        cve_ids=["CVE-TEST-0001"],
        cvss=9.0,
        contextual_score=100,
        severity="critical",
        explanation=explanation,
        match_confidence="broad",
    )


def test_retrieve_clauses_ranks_the_semantically_matching_clause_first(tmp_path):
    pack = load_pack(STUB_PACK)
    collection = ingest_pack(pack, chroma_path=str(tmp_path / "chroma"))

    finding = _finding(
        "An exposed hosting control panel (cPanel) was found directly reachable from the internet with "
        "no additional access controls.",
        product="cpanel",
        port=2083,
    )

    matches = retrieve_clauses(collection, finding, top_k=2)

    assert matches
    assert matches[0].ref == "ACME-STD 1.1"
    assert matches[0].framework_id == "ACME-STD"


def test_retrieve_clauses_returns_empty_for_empty_collection(tmp_path):
    from m516.compliance.pack_loader import CompliancePack

    empty_pack = CompliancePack(
        id="empty", display_name="Empty", home_country="ZZ", sector="test",
        frameworks=[], report_labels={}, path=tmp_path,
    )
    collection = ingest_pack(empty_pack, chroma_path=str(tmp_path / "chroma"))

    finding = _finding("anything", product="x", port=80)
    assert retrieve_clauses(collection, finding) == []
