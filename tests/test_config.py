import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from aisk.config import (
    Config,
    DEFAULT_ALIASES,
    DEFAULT_CONF_TOML,
    DEFAULT_ENV,
    DEFAULT_ENDPOINT,
    DEFAULT_SHORTCUTS,
    load_config,
    init_config,
    sync_aliases,
)


def test_default_conf_toml_matches_default_aliases():
    """DEFAULT_CONF_TOML [aliases]/[shortcuts] must equal the Python dicts.

    Guards against drift between the two sources of truth in config.py.
    """
    parsed = tomllib.loads(DEFAULT_CONF_TOML)
    assert parsed["aliases"] == DEFAULT_ALIASES
    assert parsed["shortcuts"] == DEFAULT_SHORTCUTS


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


def test_endpoint_env_override_default(monkeypatch):
    """AISK_ENDPOINT overrides the built-in default."""
    monkeypatch.setenv("AISK_ENDPOINT", "https://custom.example/v1/chat/completions")
    cfg = load_config()
    assert cfg.endpoint == "https://custom.example/v1/chat/completions"


def test_endpoint_env_overrides_conf(tmp_path, monkeypatch):
    """AISK_ENDPOINT wins over conf.toml [api] endpoint."""
    conf = tmp_path / "conf.toml"
    conf.write_text('[api]\nendpoint = "http://from-toml/v1"\n')
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setenv("AISK_ENDPOINT", "http://from-env/v1")

    cfg = load_config()
    assert cfg.endpoint == "http://from-env/v1"


def test_init_config_honors_endpoint_env(tmp_path, monkeypatch):
    """`aisk init` (non-interactive) persists AISK_ENDPOINT into conf.toml."""
    monkeypatch.setenv("AISK_ENDPOINT", "http://install-time/v1")
    init_config()
    parsed = tomllib.loads((tmp_path / "conf.toml").read_text())
    assert parsed["api"]["endpoint"] == "http://install-time/v1"


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


def test_sync_aliases_refreshes_defaults_keeps_custom(tmp_path):
    """sync drops retired defaults, refreshes current ones, keeps custom + [api]/[shortcuts]."""
    conf = tmp_path / "conf.toml"
    conf.write_text(
        '[api]\nendpoint = "http://my-host/v1"\n\n'
        "[aliases]\n"
        'clo47 = "anthropic/claude-opus-4.7"\n'   # retired → dropped
        'gpt5mini = "openai/gpt-5-mini"\n'         # retired → dropped
        'o4m = "openai/o4-mini"\n'                 # retired → dropped
        'cls46 = "anthropic/claude-sonnet-4.6"\n'  # current default → kept (as default)
        'myx = "vendor/private-model"\n'           # genuine custom → kept
        "\n[shortcuts]\n"
        'q = "qwen37"\n'
    )

    summary = sync_aliases()

    import tomllib as _t
    parsed = _t.loads(conf.read_text())
    aliases = parsed["aliases"]

    # Retired ex-defaults are gone
    for gone in ("clo47", "gpt5mini", "o4m"):
        assert gone not in aliases
    # Current defaults present (including the new ones)
    assert aliases["clo48"] == "anthropic/claude-opus-4.8"
    assert aliases["gpt54mini"] == "openai/gpt-5.4-mini"
    # Genuine custom preserved
    assert aliases["myx"] == "vendor/private-model"
    # The non-custom part equals the current defaults exactly
    assert {k: v for k, v in aliases.items() if k != "myx"} == DEFAULT_ALIASES
    # [api] and [shortcuts] untouched
    assert parsed["api"]["endpoint"] == "http://my-host/v1"
    assert parsed["shortcuts"] == {"q": "qwen37"}

    assert "clo47" in summary["removed"]
    assert "myx" in summary["kept"]
    assert "clo48" in summary["added"]


def test_sync_aliases_creates_when_missing(tmp_path):
    """sync with no conf.toml behaves like init."""
    summary = sync_aliases()
    assert (tmp_path / "conf.toml").exists()
    assert set(summary["added"]) == set(DEFAULT_ALIASES)


def test_load_config_with_shortcuts(tmp_path, monkeypatch):
    """Shortcuts section is parsed from conf.toml."""
    conf = tmp_path / "conf.toml"
    conf.write_text(
        '[api]\nendpoint = "https://openrouter.ai/api/v1/chat/completions"\n\n'
        '[shortcuts]\ngpt = "gpt55"\ncl = "cls46"\n'
    )
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)

    cfg = load_config()
    assert cfg.shortcuts["gpt"] == "gpt55"
    assert cfg.shortcuts["cl"] == "cls46"
    # Defaults are also present
    assert cfg.shortcuts["ds"] == "dsv4f"


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
