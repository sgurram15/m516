from pathlib import Path

from m516.compliance.ingest import ingest_pack
from m516.compliance.pack_loader import load_pack
from m516.compliance.retrieve import retrieve_clauses
from m516.findings import Finding
from m516.models import Asset, Service

PACK = Path(__file__).parent.parent / "packs" / "nigeria-banking"


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


def test_pack_loads_with_both_real_frameworks():
    pack = load_pack(PACK)

    assert pack.id == "nigeria-banking"
    assert pack.home_country == "NG"
    assert pack.sector == "banking"
    assert {fw.id for fw in pack.frameworks} == {"NDPR", "CBN"}


def test_ndpr_and_cbn_frameworks_have_real_clause_citations():
    pack = load_pack(PACK)
    ndpr = next(fw for fw in pack.frameworks if fw.id == "NDPR")
    cbn = next(fw for fw in pack.frameworks if fw.id == "CBN")

    assert ndpr.issuing_body == "NITDA"
    assert len(ndpr.clauses) > 0
    assert any(c.ref.startswith("NDPR Art.") for c in ndpr.clauses)

    assert "Central Bank of Nigeria" in cbn.issuing_body
    assert len(cbn.clauses) > 0
    assert any(c.ref.startswith("CBN") for c in cbn.clauses)


def test_source_documents_are_present_on_disk():
    pack = load_pack(PACK)
    for framework in pack.frameworks:
        for doc in framework.documents:
            assert (pack.path / doc).exists(), f"missing source document: {doc}"


def test_retrieve_clauses_ranks_access_control_for_exposed_admin_panel_finding(tmp_path):
    pack = load_pack(PACK)
    collection = ingest_pack(pack, chroma_path=str(tmp_path / "chroma"))

    finding = _finding(
        "An exposed hosting control panel (cPanel) with default credentials was found directly "
        "reachable from the internet with no additional access controls or authentication.",
        product="cpanel",
        port=2083,
    )

    matches = retrieve_clauses(collection, finding, top_k=3)

    assert matches
    assert "Access Control" in matches[0].ref
    assert matches[0].framework_id == "CBN"
    assert all(m.framework_id in {"NDPR", "CBN"} for m in matches)
