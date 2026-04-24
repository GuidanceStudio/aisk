import pytest


@pytest.fixture(autouse=True)
def isolate_user_config(tmp_path, monkeypatch):
    """Prevent tests from accidentally reading the real ~/.aisk/ of the dev machine.

    Tests that need config files create their own via monkeypatch + write_text.
    This fixture only redirects the default paths to an empty tmp dir, so that
    `load_config()` falls back to coded defaults in tests that don't set up a conf.
    """
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("AISK_API_KEY", raising=False)
