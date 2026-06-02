from aisk import session


def test_save_load_roundtrip():
    session.save_session("m", [{"role": "user", "content": "hi"}], key="A", now=100.0)
    s = session.load_session(key="A", now=101.0)
    assert s["model"] == "m"
    assert s["messages"] == [{"role": "user", "content": "hi"}]


def test_load_prefers_own_key_over_recent():
    session.save_session("ma", [{"role": "user", "content": "a"}], key="A", now=100.0)
    session.save_session("mb", [{"role": "user", "content": "b"}], key="B", now=200.0)
    # A has its own session → it wins over the (more recent) B.
    s = session.load_session(key="A", now=300.0)
    assert s["model"] == "ma"


def test_fallback_picks_most_recent():
    session.save_session("ma", [{"role": "user", "content": "a"}], key="A", now=100.0)
    session.save_session("mb", [{"role": "user", "content": "b"}], key="B", now=200.0)
    # A fresh terminal (no own session) resumes the most recent one.
    s = session.load_session(key="C", now=300.0)
    assert s["model"] == "mb"


def test_load_none_when_empty():
    assert session.load_session(key="X", now=1.0) is None


def test_prune_removes_old_on_save():
    session.save_session("old", [{"role": "user", "content": "x"}], key="OLD", now=0.0)
    session.save_session(
        "new", [{"role": "user", "content": "y"}], key="NEW", now=session.SESSION_TTL + 10
    )
    files = sorted(f.stem for f in session._sessions_dir().glob("*.json"))
    assert files == ["NEW"]


def test_sessions_dir_is_private():
    import os
    import stat
    session.save_session("m", [{"role": "user", "content": "x"}], key="A", now=1.0)
    mode = stat.S_IMODE(os.stat(session._sessions_dir()).st_mode)
    assert mode == 0o700


def test_load_skips_corrupted(tmp_path):
    d = session._sessions_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "BAD.json").write_text("{ not json")
    assert session.load_session(key="BAD", now=1.0) is None
