import logging
import subprocess
import sys

from m516.config import load_config
from m516.logging import get_logger


def test_config_loads_with_sane_defaults(monkeypatch):
    monkeypatch.delenv("NETLAS_API_KEY", raising=False)
    monkeypatch.delenv("CRIMINALIP_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    config = load_config()

    assert config.log_level == "INFO"
    assert config.database_url is None
    assert config.netlas_api_key is None
    assert config.criminalip_api_key is None


def test_config_reads_present_env_vars(monkeypatch):
    monkeypatch.setenv("NETLAS_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    config = load_config()

    assert config.netlas_api_key == "test-key"
    assert config.log_level == "DEBUG"


def test_get_logger_returns_named_logger():
    logger = get_logger("m516.test")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "m516.test"


def test_cli_help_exits_cleanly():
    result = subprocess.run(
        [sys.executable, "-m", "m516", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "m516" in result.stdout
