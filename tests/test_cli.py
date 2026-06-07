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
    out = capsys.readouterr().out
    assert "commands:" in out
    assert "init          create ~/.aisk config" in out
    assert "sync          refresh default aliases" in out
    assert "models        list configured model aliases" in out
    assert "completions   generate, install, or refresh shell completions" in out
    assert "aisk cls46" in out


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
    assert "ge31lite" in out
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
            assert main(["ge31lite", "hello"]) == 1
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
                assert main(["ge31lite", "hello"]) == 0

    assert "wizard-reply" in capsys.readouterr().out


def test_model_and_message_verbose(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("answer"), UsageInfo(prompt_tokens=5, completion_tokens=2))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["ge31lite", "hello"]) == 0
    out = capsys.readouterr().out
    assert "answer" in out
    assert "ANSWER" in out


def test_quiet_flag(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("quiet answer"))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["-q", "ge31lite", "hello"]) == 0
    out = capsys.readouterr().out
    assert out == "quiet answer\n"
    assert "ANSWER" not in out


def test_model_no_message_tty_enters_chat(monkeypatch):
    """No message on a TTY → interactive chat."""
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    called = {}

    def fake_chat(model, cfg, **kw):
        called["model"] = model
        return 0

    with patch("aisk.cli.sys.stdin") as mock_stdin, \
         patch("aisk.cli.chat", fake_chat):
        mock_stdin.isatty.return_value = True
        assert main(["ge31lite"]) == 0
    assert called["model"] == "google/gemini-3.1-flash-lite-preview"


def test_model_stdin_message(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("from-stdin-reply"))
    with patch("aisk.cli.stream_chat", mock), \
         patch("aisk.cli.sys.stdin", io.StringIO("from stdin")):
        assert main(["ge31lite"]) == 0
    assert "from-stdin-reply" in capsys.readouterr().out


def test_model_empty_stdin():
    with patch("aisk.cli.sys.stdin", io.StringIO("")):
        assert main(["ge31lite"]) == 2


def test_passthrough_model(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("perplexity reply"))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["perplexity/sonar", "test"]) == 0
    out = capsys.readouterr().out
    assert "perplexity/sonar" in out


def test_no_stream_verbose(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("buffered"), UsageInfo(prompt_tokens=1, completion_tokens=1))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["-S", "ge31lite", "hello"]) == 0
    out = capsys.readouterr().out
    assert "buffered" in out
    assert "ANSWER" in out


def test_no_stream_quiet(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("buffered quiet"))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["-q", "-S", "ge31lite", "hello"]) == 0
    out = capsys.readouterr().out
    assert out == "buffered quiet\n"
    assert "ANSWER" not in out


def test_oneshot_persists_session(monkeypatch):
    """A one-shot call saves the exchange so it can be resumed."""
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    mock = _mock_stream(ContentChunk("answer"))
    with patch("aisk.cli.stream_chat", mock):
        assert main(["dsv4f", "ciao"]) == 0
    from aisk import session
    s = session.load_session()
    assert s["model"] == "deepseek/deepseek-v4-flash"
    assert s["messages"] == [
        {"role": "user", "content": "ciao"},
        {"role": "assistant", "content": "answer"},
    ]


def test_resume_no_session_errors(capsys, monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    assert main(["--resume"]) == 1
    assert "nothing to resume" in capsys.readouterr().err.lower()


def test_resume_oneshot_continuation(monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    from aisk import session
    session.save_session(
        "deepseek/deepseek-v4-flash",
        [{"role": "user", "content": "ciao"}, {"role": "assistant", "content": "hey"}],
    )
    received = {}

    def cap(endpoint, api_key, model, messages, **kw):
        received["model"] = model
        received["messages"] = [m.copy() for m in messages]
        yield ContentChunk("more")

    with patch("aisk.cli.stream_chat", cap):
        assert main(["--resume", "e", "poi?"]) == 0

    assert received["model"] == "deepseek/deepseek-v4-flash"
    assert received["messages"][0] == {"role": "user", "content": "ciao"}
    assert received["messages"][-1] == {"role": "user", "content": "e poi?"}
    # session grew with the new exchange
    s = session.load_session()
    assert s["messages"][-1] == {"role": "assistant", "content": "more"}


def test_resume_interactive_preloads_history(monkeypatch):
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    from aisk import session
    hist = [{"role": "user", "content": "ciao"}, {"role": "assistant", "content": "hey"}]
    session.save_session("some/model", hist)
    called = {}

    def fake_chat(model, cfg, **kw):
        called["model"] = model
        called["history"] = kw.get("history")
        return 0

    with patch("aisk.cli.chat", fake_chat), patch("aisk.cli.sys.stdin") as st:
        st.isatty.return_value = True
        assert main(["--resume"]) == 0

    assert called["model"] == "some/model"
    assert called["history"] == hist


def test_multiword_message_without_quotes(capsys, monkeypatch):
    """aisk ge3flash what is the CAP theorem — joins all words after model."""
    monkeypatch.setenv("AISK_API_KEY", "test-key")
    received = {}

    def capture_stream(endpoint, api_key, model, messages, **kw):
        received["messages"] = messages
        yield ContentChunk("reply")

    with patch("aisk.cli.stream_chat", capture_stream):
        assert main(["ge31lite", "what", "is", "the", "CAP", "theorem"]) == 0
    assert received["messages"] == [{"role": "user", "content": "what is the CAP theorem"}]
