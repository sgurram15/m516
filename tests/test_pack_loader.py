from pathlib import Path

import pytest

from m516.compliance.pack_loader import PackLoadError, load_pack

STUB_PACK = Path(__file__).parent / "fixtures" / "packs" / "test-stub"


def test_load_pack_parses_pack_yaml_fields():
    pack = load_pack(STUB_PACK)

    assert pack.id == "test-stub"
    assert pack.home_country == "ZZ"
    assert pack.sector == "fictional"
    assert pack.report_labels["primary_regulator"].startswith("ACME")


def test_load_pack_parses_framework_and_clauses():
    pack = load_pack(STUB_PACK)

    assert len(pack.frameworks) == 1
    framework = pack.frameworks[0]
    assert framework.id == "ACME-STD"
    assert framework.issuing_body == "ACME Regulatory Authority (fictional)"
    assert framework.documents == ["documents/acme.txt"]
    assert len(framework.clauses) == 4

    admin_clause = next(c for c in framework.clauses if c.ref == "ACME-STD 1.1")
    assert admin_clause.title == "No exposed administrative interfaces"
    assert "admin panel" in admin_clause.finding_hints


def test_load_pack_raises_on_missing_pack_yaml(tmp_path):
    with pytest.raises(PackLoadError, match="missing required file"):
        load_pack(tmp_path)


def test_load_pack_raises_on_malformed_pack_yaml(tmp_path):
    # frameworks: [] provided so the field actually under test — display_name — is what trips first;
    # frameworks is validated earlier in load_pack() than display_name is.
    (tmp_path / "pack.yaml").write_text("id: broken\nframeworks: []\n", encoding="utf-8")

    with pytest.raises(PackLoadError, match="display_name"):
        load_pack(tmp_path)


def test_load_pack_raises_on_clause_missing_required_field(tmp_path):
    (tmp_path / "frameworks").mkdir()
    (tmp_path / "pack.yaml").write_text(
        "id: broken\ndisplay_name: X\nhome_country: ZZ\nsector: test\nframeworks: [bad]\n",
        encoding="utf-8",
    )
    (tmp_path / "frameworks" / "bad.yaml").write_text(
        "id: BAD\ndisplay_name: X\nissuing_body: X\ndocuments: [d.txt]\n"
        "clauses:\n  - ref: X\n    title: X\n",  # missing 'summary'
        encoding="utf-8",
    )

    with pytest.raises(PackLoadError, match="summary"):
        load_pack(tmp_path)
