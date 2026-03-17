import os
from pathlib import Path

from aisk.config import (
    Config,
    DEFAULT_ALIASES,
    DEFAULT_CONF_TOML,
    DEFAULT_ENV,
    DEFAULT_ENDPOINT,
    DEFAULT_SHORTCUTS,
    load_config,
    init_config,
)


def test_default_config():
    cfg = Config()
    assert cfg.endpoint == DEFAULT_ENDPOINT
    assert cfg.api_key == ""
    assert cfg.aliases == DEFAULT_ALIASES
    assert cfg.shortcuts == DEFAULT_SHORTCUTS


def test_load_config_no_files(tmp_path, monkeypatch):
    """When no config files exist, returns defaults."""
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    cfg = load_config()
    assert cfg.endpoint == DEFAULT_ENDPOINT
    assert cfg.api_key == ""
    assert cfg.aliases == DEFAULT_ALIASES


def test_load_config_with_files(tmp_path, monkeypatch):
    """Config file overrides endpoint and adds aliases."""
    conf = tmp_path / "conf.toml"
    conf.write_text(
        '[api]\nendpoint = "http://localhost:8080/v1/chat/completions"\n\n'
        '[aliases]\nmymodel = "custom/model-v1"\n'
    )
    env = tmp_path / ".env"
    env.write_text("AISK_API_KEY=test-key-123\n")

    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", env)
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    cfg = load_config()
    assert cfg.endpoint == "http://localhost:8080/v1/chat/completions"
    assert cfg.api_key == "test-key-123"
    assert cfg.aliases["mymodel"] == "custom/model-v1"
    # Default aliases still present
    assert "ge31lite" in cfg.aliases


def test_load_config_env_override(tmp_path, monkeypatch):
    """Environment variable takes precedence."""
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.setenv("AISK_API_KEY", "env-key")

    cfg = load_config()
    assert cfg.api_key == "env-key"


def test_init_config_creates_files(tmp_path, monkeypatch):
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")

    actions = init_config()
    assert len(actions) == 2
    assert "Created" in actions[0]
    assert "Created" in actions[1]
    assert (tmp_path / "conf.toml").exists()
    assert (tmp_path / ".env").exists()
    assert (tmp_path / "conf.toml").read_text() == DEFAULT_CONF_TOML
    assert "[shortcuts]" in (tmp_path / "conf.toml").read_text()
    assert (tmp_path / ".env").read_text() == DEFAULT_ENV


def test_init_config_skips_existing(tmp_path, monkeypatch):
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")

    (tmp_path / "conf.toml").write_text("existing")
    (tmp_path / ".env").write_text("existing")

    actions = init_config()
    assert all("Skipped" in a for a in actions)
    assert (tmp_path / "conf.toml").read_text() == "existing"


def test_load_config_with_shortcuts(tmp_path, monkeypatch):
    """Shortcuts section is parsed from conf.toml."""
    conf = tmp_path / "conf.toml"
    conf.write_text(
        '[api]\nendpoint = "https://openrouter.ai/api/v1/chat/completions"\n\n'
        '[shortcuts]\ngpt = "gpt54"\ncl = "cls46"\n'
    )
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    cfg = load_config()
    assert cfg.shortcuts["gpt"] == "gpt54"
    assert cfg.shortcuts["cl"] == "cls46"
    # Defaults are also present
    assert cfg.shortcuts["ds"] == "dsv32"


def test_load_config_no_shortcuts_section(tmp_path, monkeypatch):
    """Config without [shortcuts] uses defaults."""
    conf = tmp_path / "conf.toml"
    conf.write_text('[api]\nendpoint = "https://openrouter.ai/api/v1/chat/completions"\n')
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    cfg = load_config()
    assert cfg.shortcuts == DEFAULT_SHORTCUTS
