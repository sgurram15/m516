import m516.discovery as discovery_module
from m516.discovery import run_discovery
from m516.models import Asset, Service
from m516.providers.base import BaseProvider


class _FakeProvider(BaseProvider):
    def __init__(self, name, assets=None, error=None):
        self.name = name
        self._assets = assets or []
        self._error = error

    def discover(self, domain):
        if self._error:
            raise self._error
        return self._assets


def test_run_discovery_merges_assets_from_multiple_providers(monkeypatch):
    providers = [
        _FakeProvider("a", assets=[Asset(ip="1.2.3.4", services=[Service(port=443, protocol="tcp")])]),
        _FakeProvider("b", assets=[Asset(ip="1.2.3.4", services=[Service(port=22, protocol="tcp")])]),
    ]
    monkeypatch.setattr(discovery_module, "get_enabled_providers", lambda config: providers)

    result = run_discovery("example.com")

    assert result.domain == "example.com"
    assert len(result.assets) == 1
    assert {s.port for s in result.assets[0].services} == {443, 22}
    assert result.errors == []


def test_run_discovery_records_error_and_continues_when_one_provider_fails(monkeypatch):
    providers = [
        _FakeProvider("broken", error=RuntimeError("boom")),
        _FakeProvider("ok", assets=[Asset(ip="1.2.3.4")]),
    ]
    monkeypatch.setattr(discovery_module, "get_enabled_providers", lambda config: providers)

    result = run_discovery("example.com")

    assert len(result.errors) == 1
    assert "broken" in result.errors[0]
    assert len(result.assets) == 1


def test_run_discovery_applies_waf_detection(monkeypatch):
    providers = [_FakeProvider("a", assets=[Asset(ip="1.2.3.4", as_name="CLOUDFLARENET")])]
    monkeypatch.setattr(discovery_module, "get_enabled_providers", lambda config: providers)

    result = run_discovery("example.com")

    assert result.assets[0].is_behind_waf is True
