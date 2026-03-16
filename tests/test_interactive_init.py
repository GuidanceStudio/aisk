from pathlib import Path

from aisk.config import (
    DEFAULT_CONF_TOML,
    DEFAULT_ENDPOINT,
    interactive_init,
    _mask_key,
    _read_existing_key,
)


def _make_input(*responses):
    """Create an input function that returns responses in order."""
    it = iter(responses)
    return lambda prompt: next(it)


def _setup(tmp_path, monkeypatch):
    """Point config paths to tmp_path."""
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    return tmp_path


class TestMaskKey:
    def test_short_key(self):
        assert _mask_key("abc") == "****"

    def test_long_key(self):
        assert _mask_key("sk-or-abcdef123456") == "sk-or-...3456"


class TestReadExistingKey:
    def test_no_file(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        assert _read_existing_key() == ""

    def test_with_key(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        (tmp_path / ".env").write_text("AISK_API_KEY=my-secret-key\n")
        assert _read_existing_key() == "my-secret-key"

    def test_empty_key(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        (tmp_path / ".env").write_text("AISK_API_KEY=\n")
        assert _read_existing_key() == ""


class TestInteractiveInitFreshSetup:
    def test_creates_both_files(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        output = []
        interactive_init(
            input_fn=_make_input("", "test-api-key"),  # default endpoint, api key
            print_fn=lambda msg: output.append(msg),
        )
        assert (tmp_path / "conf.toml").exists()
        assert (tmp_path / ".env").exists()
        assert "test-api-key" in (tmp_path / ".env").read_text()
        assert DEFAULT_ENDPOINT in (tmp_path / "conf.toml").read_text()
        assert any("Configuration saved" in m for m in output)

    def test_custom_endpoint(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        output = []
        interactive_init(
            input_fn=_make_input("http://localhost:8080/v1/chat/completions", "key"),
            print_fn=lambda msg: output.append(msg),
        )
        content = (tmp_path / "conf.toml").read_text()
        assert "localhost:8080" in content
        assert DEFAULT_ENDPOINT not in content

    def test_empty_api_key(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        output = []
        interactive_init(
            input_fn=_make_input("", ""),  # default endpoint, empty key
            print_fn=lambda msg: output.append(msg),
        )
        assert (tmp_path / ".env").exists()
        assert any("empty key" in m for m in output)


class TestInteractiveInitExistingConfig:
    def test_skip_conf_skip_env(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        (tmp_path / "conf.toml").write_text("existing")
        (tmp_path / ".env").write_text("AISK_API_KEY=old-key\n")
        output = []
        interactive_init(
            input_fn=_make_input("n", "n"),  # don't overwrite either
            print_fn=lambda msg: output.append(msg),
        )
        assert (tmp_path / "conf.toml").read_text() == "existing"
        assert "old-key" in (tmp_path / ".env").read_text()
        assert any("Skipped conf.toml" in m for m in output)
        assert any("Skipped .env" in m for m in output)

    def test_overwrite_conf(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        (tmp_path / "conf.toml").write_text("old content")
        (tmp_path / ".env").write_text("AISK_API_KEY=old-key\n")
        output = []
        interactive_init(
            input_fn=_make_input("y", "", "n"),  # overwrite conf, default endpoint, skip env
            print_fn=lambda msg: output.append(msg),
        )
        assert DEFAULT_ENDPOINT in (tmp_path / "conf.toml").read_text()
        assert any("Wrote" in m for m in output)

    def test_overwrite_env(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        (tmp_path / "conf.toml").write_text("existing")
        (tmp_path / ".env").write_text("AISK_API_KEY=old-key\n")
        output = []
        interactive_init(
            input_fn=_make_input("n", "y", "new-key"),  # skip conf, overwrite env, new key
            print_fn=lambda msg: output.append(msg),
        )
        assert "new-key" in (tmp_path / ".env").read_text()
        assert any("updated" in m for m in output)

    def test_overwrite_env_empty_keeps_existing(self, tmp_path, monkeypatch):
        _setup(tmp_path, monkeypatch)
        (tmp_path / "conf.toml").write_text("existing")
        (tmp_path / ".env").write_text("AISK_API_KEY=old-key\n")
        output = []
        interactive_init(
            input_fn=_make_input("n", "y", ""),  # skip conf, overwrite env, empty key
            print_fn=lambda msg: output.append(msg),
        )
        assert "old-key" in (tmp_path / ".env").read_text()
        assert any("kept existing" in m for m in output)
