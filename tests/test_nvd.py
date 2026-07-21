import json
from pathlib import Path

from m516.enrichment.nvd import _build_query, from_records
from m516.models import Service

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    with (FIXTURES / name).open() as fh:
        return json.load(fh)


def test_from_records_parses_cve_with_v31_metrics():
    matches = from_records(_load("nvd_log4j.json"), match_confidence="exact")

    assert len(matches) == 1
    match = matches[0]
    assert match.id == "CVE-2021-44228"
    assert match.cvss_score == 10.0
    assert match.cvss_severity == "CRITICAL"
    assert match.published.year == 2021
    assert "JNDI" in match.description
    assert match.match_confidence == "exact"
    assert match.exploitability_score == 3.9
    assert match.impact_score == 6.0


def test_from_records_defaults_to_broad_confidence():
    matches = from_records(_load("nvd_log4j.json"))

    assert matches[0].match_confidence == "broad"


def test_from_records_handles_empty_results():
    assert from_records(_load("nvd_empty.json")) == []


def test_from_records_handles_empty_response():
    assert from_records({}) == []


def test_from_records_falls_back_to_cvss_v2_when_v3_absent():
    data = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2000-0001",
                    "published": "1999-01-01T00:00:00.000",
                    "descriptions": [{"lang": "en", "value": "old vuln"}],
                    "metrics": {
                        "cvssMetricV2": [
                            {
                                "cvssData": {"baseScore": 7.5},
                                "baseSeverity": "HIGH",
                                "exploitabilityScore": 8.6,
                                "impactScore": 6.4,
                            }
                        ]
                    },
                }
            }
        ]
    }

    matches = from_records(data)

    assert matches[0].cvss_score == 7.5
    assert matches[0].cvss_severity == "HIGH"
    assert matches[0].exploitability_score == 8.6
    assert matches[0].impact_score == 6.4


def test_build_query_uses_cpe_name_for_versioned_cpe():
    service = Service(port=25, protocol="tcp", cpe="cpe:2.3:a:f5:nginx:1.18.0:*:*:*:*:*:*:*")

    params, cache_key, confidence = _build_query(service)

    assert "cpeName" in params
    assert cache_key.startswith("cpeName:")
    assert confidence == "exact"


def test_build_query_uses_virtual_match_string_for_wildcarded_cpe():
    service = Service(port=25, protocol="tcp", cpe="cpe:2.3:a:f5:nginx:*:*:*:*:*:*:*:*")

    params, cache_key, confidence = _build_query(service)

    assert "virtualMatchString" in params
    assert cache_key.startswith("virtualMatchString:")
    assert confidence == "broad"


def test_build_query_falls_back_to_keyword_search_without_cpe():
    service = Service(port=25, protocol="tcp", product="MailEnable", version="10.57")

    params, cache_key, confidence = _build_query(service)

    assert params["keywordSearch"] == "MailEnable 10.57"
    assert cache_key.startswith("keywordSearch:")
    assert confidence == "broad"


def test_build_query_returns_none_when_not_cve_eligible():
    service = Service(port=25, protocol="tcp")

    params, cache_key, confidence = _build_query(service)

    assert params is None
    assert cache_key is None
    assert confidence is None
