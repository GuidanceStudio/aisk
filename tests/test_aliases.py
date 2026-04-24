from aisk.aliases import resolve_model
from aisk.config import DEFAULT_ALIASES


def test_known_alias():
    assert resolve_model("ge31lite", DEFAULT_ALIASES) == "google/gemini-3.1-flash-lite-preview"


def test_unknown_passthrough():
    assert resolve_model("perplexity/sonar", DEFAULT_ALIASES) == "perplexity/sonar"


def test_custom_alias():
    custom = {"mymodel": "vendor/custom-v1"}
    assert resolve_model("mymodel", custom) == "vendor/custom-v1"
    assert resolve_model("other", custom) == "other"


def test_perplexity_aliases():
    assert resolve_model("s", DEFAULT_ALIASES) == "perplexity/sonar"
    assert resolve_model("sps", DEFAULT_ALIASES) == "perplexity/sonar-pro-search"


def test_new_aliases_apr_2026():
    """M22: April 2026 refresh — new/updated aliases point to current models."""
    assert resolve_model("clo47", DEFAULT_ALIASES) == "anthropic/claude-opus-4.7"
    assert resolve_model("gpt55", DEFAULT_ALIASES) == "openai/gpt-5.5"
    assert resolve_model("gpt55pro", DEFAULT_ALIASES) == "openai/gpt-5.5-pro"
    assert resolve_model("dsv4f", DEFAULT_ALIASES) == "deepseek/deepseek-v4-flash"
    assert resolve_model("dsv4p", DEFAULT_ALIASES) == "deepseek/deepseek-v4-pro"
    assert resolve_model("glm51", DEFAULT_ALIASES) == "z-ai/glm-5.1"
    assert resolve_model("m27", DEFAULT_ALIASES) == "minimax/minimax-m2.7"
    assert resolve_model("kimi26", DEFAULT_ALIASES) == "moonshotai/kimi-k2.6"
    assert resolve_model("qwen36p", DEFAULT_ALIASES) == "qwen/qwen3.6-plus"


def test_retained_aliases():
    """Aliases kept from the previous catalog (still current in apr 2026)."""
    assert resolve_model("cls46", DEFAULT_ALIASES) == "anthropic/claude-sonnet-4.6"
    assert resolve_model("clh45", DEFAULT_ALIASES) == "anthropic/claude-haiku-4.5"
    assert resolve_model("ge31lite", DEFAULT_ALIASES) == "google/gemini-3.1-flash-lite-preview"
    assert resolve_model("ge31pro", DEFAULT_ALIASES) == "google/gemini-3.1-pro-preview"


def test_removed_aliases_passthrough():
    """Aliases removed in M22 must not resolve — they pass through unchanged."""
    removed = (
        "clo46",    # → clo47
        "gpt54",    # → gpt55
        "dsv32",    # → dsv4f
        "dsr1",     # → dsv4p
        "glm5",     # → glm51
        "m25",      # → m27
        "qwen35p",  # → qwen36p
        "qwen35",   # dropped (no direct successor)
        # already stale before M22, still stale:
        "gpt5", "gpt51", "gpt52", "ge25lite", "k25", "ge3flash",
    )
    for alias in removed:
        assert resolve_model(alias, DEFAULT_ALIASES) == alias, f"{alias} should not resolve"


def test_all_default_aliases_resolve():
    for alias, full_name in DEFAULT_ALIASES.items():
        assert resolve_model(alias, DEFAULT_ALIASES) == full_name
