import tomllib
import sys

from aisk.config import Config, load_config, _render_default_conf


def test_default_model_defaults_to_dsf():
    """Config has default_model='dsf' out of the box."""
    cfg = Config()
    assert cfg.default_model == "dsf"


def test_default_model_from_conf_toml(tmp_path, monkeypatch):
    """default_model is read from the [defaults] section in conf.toml."""
    conf = tmp_path / "conf.toml"
    env = tmp_path / ".env"
    conf.write_text('[defaults]\nmodel = "gef"\n[api]\nendpoint = "https://example.com/api"\n')
    env.write_text("AISK_API_KEY=test-key\n")

    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", env)

    cfg = load_config()
    assert cfg.default_model == "gef"


def test_default_model_missing_defaults_section(tmp_path, monkeypatch):
    """When [defaults] section is missing, default_model stays 'dsf'."""
    conf = tmp_path / "conf.toml"
    env = tmp_path / ".env"
    conf.write_text('[api]\nendpoint = "https://example.com/api"\n')
    env.write_text("AISK_API_KEY=test-key\n")

    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", conf)
    monkeypatch.setattr("aisk.config.ENV_FILE", env)

    cfg = load_config()
    assert cfg.default_model == "dsf"


def test_default_conf_toml_has_defaults_section():
    """The generated default conf.toml template includes a [defaults] section."""
    rendered = _render_default_conf()
    assert "[defaults]" in rendered
    assert 'model = "dsf"' in rendered
