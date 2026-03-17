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


def test_new_aliases():
    assert resolve_model("gpt54", DEFAULT_ALIASES) == "openai/gpt-5.4"
    assert resolve_model("clh45", DEFAULT_ALIASES) == "anthropic/claude-haiku-4.5"


def test_updated_aliases():
    assert resolve_model("dsr1", DEFAULT_ALIASES) == "deepseek/deepseek-r1"


def test_removed_aliases_passthrough():
    """Removed aliases should not resolve — they pass through as-is."""
    for alias in ("gpt5", "gpt51", "gpt52", "ge25lite", "k25", "ge3flash"):
        assert resolve_model(alias, DEFAULT_ALIASES) == alias


def test_all_default_aliases_resolve():
    for alias, full_name in DEFAULT_ALIASES.items():
        assert resolve_model(alias, DEFAULT_ALIASES) == full_name
