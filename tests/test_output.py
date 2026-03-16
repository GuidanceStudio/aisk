from aisk.client import ContentChunk, ErrorInfo, ReasoningChunk, UsageInfo
from aisk.output import render_quiet, render_verbose


def _events(*items):
    yield from items


def test_verbose_content_only(capsys):
    events = _events(
        ContentChunk("Hello "),
        ContentChunk("world"),
        UsageInfo(prompt_tokens=5, completion_tokens=2),
    )
    rc = render_verbose("test/model", "hi", events)
    assert rc == 0
    out = capsys.readouterr().out
    assert "test/model" in out
    assert "ANSWER" in out
    assert "Hello world" in out
    assert "In 5" in out
    assert "Out 2" in out


def test_verbose_with_reasoning(capsys):
    events = _events(
        ReasoningChunk("thinking..."),
        ContentChunk("answer"),
        UsageInfo(prompt_tokens=5, completion_tokens=2, reasoning_tokens=10),
    )
    rc = render_verbose("test/model", "q", events)
    assert rc == 0
    out = capsys.readouterr().out
    assert "THINKING" in out
    assert "thinking..." in out
    assert "ANSWER" in out
    assert "answer" in out
    assert "Reasoning: 10" in out


def test_verbose_with_cost(capsys):
    events = _events(
        ContentChunk("ok"),
        UsageInfo(prompt_tokens=1, completion_tokens=1, cost=0.0123),
    )
    rc = render_verbose("m", "q", events)
    assert rc == 0
    out = capsys.readouterr().out
    assert "$0.012300" in out


def test_verbose_error(capsys):
    events = _events(ErrorInfo(message="rate limited"))
    rc = render_verbose("m", "q", events)
    assert rc == 1
    out = capsys.readouterr().out
    assert "rate limited" in out


def test_quiet_content_only(capsys):
    events = _events(
        ContentChunk("Hello "),
        ContentChunk("world"),
        UsageInfo(prompt_tokens=5, completion_tokens=2),
    )
    rc = render_quiet(events)
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "Hello world\n"
    # No ANSI, no decoration
    assert "\033[" not in out
    assert "ANSWER" not in out
    assert "Tokens" not in out


def test_quiet_skips_reasoning(capsys):
    events = _events(
        ReasoningChunk("thinking..."),
        ContentChunk("answer"),
    )
    rc = render_quiet(events)
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "answer\n"
    assert "thinking" not in out


def test_quiet_error(capsys):
    events = _events(ErrorInfo(message="fail"))
    rc = render_quiet(events)
    assert rc == 1
    err = capsys.readouterr().err
    assert "fail" in err
