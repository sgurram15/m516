from pathlib import Path

from m516.compliance.ingest import ingest_pack
from m516.compliance.pack_loader import load_pack

STUB_PACK = Path(__file__).parent / "fixtures" / "packs" / "test-stub"


def test_ingest_pack_embeds_every_clause(tmp_path):
    pack = load_pack(STUB_PACK)

    collection = ingest_pack(pack, chroma_path=str(tmp_path / "chroma"))

    assert collection.count() == 4
    stored = collection.get(ids=["ACME-STD 1.1"])
    assert "administrative interfaces" in stored["documents"][0].lower() or "admin panel" in stored["documents"][0].lower()
    assert stored["metadatas"][0]["framework_id"] == "ACME-STD"


def test_ingest_pack_is_idempotent_on_rerun(tmp_path):
    pack = load_pack(STUB_PACK)
    chroma_path = str(tmp_path / "chroma")

    ingest_pack(pack, chroma_path=chroma_path)
    collection = ingest_pack(pack, chroma_path=chroma_path)

    assert collection.count() == 4  # re-ingesting upserts, doesn't duplicate
