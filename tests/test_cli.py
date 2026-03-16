import io
from unittest.mock import patch

from aisk import __version__
from aisk.cli import main
from aisk.client import ContentChunk, UsageInfo


def _mock_stream(*events):
    """Return a mock stream_chat that yields given events."""
    def fake_stream(endpoint, api_key, model, message, **kw):
        yield from events
    return fake_stream


def test_version(capsys):
    try:
        main(["--version"])
    except SystemExit:
        pass
    assert __version__ in capsys.readouterr().out


def test_no_args_returns_2(capsys):
    assert main([]) == 2


def test_init_subcommand(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr("aisk.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("aisk.config.CONFIG_FILE", tmp_path / "conf.toml")
    monkeypatch.setattr("aisk.config.ENV_FILE", tmp_path / ".env")
    assert main(["init"]) == 0
    assert "Created" in capsys.readouterr().out


def test_models_subcommand(capsys):
    assert main(["models"]) == 0
    out = capsys.readouterr().out
    # Check grouped output
    assert "Google" in out
    assert "ge3flash" in out
    assert "google/gemini" in out
    assert "Perplexity" in out
    assert "Anthropic" in out
    assert "Openai" in out


def test_no_api_key_non_tty(capsys, monkeypatch):
    """Non-TTY with no API key → error with helpful message."""
    monkeypatch.delenv("AISK_API_KEY", raising=False)
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        monkeypatch.setattr("aisk.config.CONFIG_DIR", p)
        monkeypatch.setattr("aisk.config.CONFIG_FILE", p / "conf.toml")
        monkeypatch.setattr("aisk.config.ENV_FILE", p / ".env")
        with patch("aisk.config.sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            assert main(["ge3flash", "hello"]) == 1
    assert "AISK_API_KEY" in capsys.readouterr().err


def test_auto_init_first_run(capsys, monkeypatch):
    """First run with no config + TTY → auto-launches wizard, then proceeds."""
    monkeypatch.delenv("AISK_API_KEY", raising=False)
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        monkeypatch.setattr("aisk.config.CONFIG_DIR", p)
        monkeypatch.setattr("aisk.config.CONFIG_FILE", p / "conf.toml")
        monkeypatch.setattr("aisk.config.ENV_FILE", p / ".env")

        # Mock TTY + interactive_init that writes a key
        with patch("aisk.config.sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True

            def fake_init(input_fn=None, print_fn=None, *, auto=False):
                # Simulate wizard writing config files
                (p / "conf.toml").write_text('[api]\nendpoint = "https://openrouter.ai/api/v1/chat/completions"\n[aliases]\n')
                (p / ".env").write_text("AISK_API_KEY=test-wizard-key\n")

            monkeypatch.setattr("aisk.config.interactive_init", fake_init)

            mock = _mock_stream(ContentChunk("wizard-reply"))
            with patch("aisk.cli.stream_chat", mock):
                assert main(["ge3flash", "hello"]) == 0

    assert "wizard-reply" in capsys.readouterr().out


def test_model_and_message_verbose(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("answer"), UsageInfo(prompt_tokens=5, completion_tokens=2))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["ge3flash", "hello"]) == 0
    out = capsys.readouterr().out
    assert "answer" in out
    assert "ANSWER" in out


def test_quiet_flag(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("quiet answer"))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["-q", "ge3flash", "hello"]) == 0
    out = capsys.readouterr().out
    assert out == "quiet answer\n"
    assert "ANSWER" not in out


def test_model_no_message_tty(capsys):
    with patch("aisk.cli.sys.stdin") as mock_stdin:
        mock_stdin.isatty.return_value = True
        assert main(["ge3flash"]) == 2


def test_model_stdin_message(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("from-stdin-reply"))
    with patch("aisk.cli.stream_chat", mock), \
         patch("aisk.cli.sys.stdin", io.StringIO("from stdin")):
        assert main(["ge3flash"]) == 0
    assert "from-stdin-reply" in capsys.readouterr().out


def test_model_empty_stdin():
    with patch("aisk.cli.sys.stdin", io.StringIO("")):
        assert main(["ge3flash"]) == 2


def test_passthrough_model(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("perplexity reply"))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["perplexity/sonar", "test"]) == 0
    out = capsys.readouterr().out
    assert "perplexity/sonar" in out


def test_multiword_message_without_quotes(capsys, monkeypatch):
    """aisk ge3flash what is the CAP theorem — joins all words after model."""
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    received = {}

    def capture_stream(endpoint, api_key, model, message, **kw):
        received["message"] = message
        yield ContentChunk("reply")

    with patch("aisk.cli.stream_chat", capture_stream):
        assert main(["ge3flash", "what", "is", "the", "CAP", "theorem"]) == 0
    assert received["message"] == "what is the CAP theorem"
