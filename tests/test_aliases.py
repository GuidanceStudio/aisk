from aisk.aliases import resolve_model
from aisk.config import ALIAS_RENAMES, DEFAULT_ALIASES, RETIRED_ALIASES


def test_known_alias():
    assert resolve_model("gel", DEFAULT_ALIASES) == "google/gemini-3.1-flash-lite-preview"


def test_unknown_passthrough():
    assert resolve_model("perplexity/sonar", DEFAULT_ALIASES) == "perplexity/sonar"


def test_custom_alias():
    custom = {"mymodel": "vendor/custom-v1"}
    assert resolve_model("mymodel", custom) == "vendor/custom-v1"
    assert resolve_model("other", custom) == "other"


def test_perplexity_aliases():
    assert resolve_model("s", DEFAULT_ALIASES) == "perplexity/sonar"
    assert resolve_model("sps", DEFAULT_ALIASES) == "perplexity/sonar-pro-search"


def test_new_aliases_jun_2026():
    """M24/M28: June 2026 refresh — new/updated aliases point to current models."""
    assert resolve_model("clo", DEFAULT_ALIASES) == "anthropic/claude-opus-4.8"
    assert resolve_model("qwen", DEFAULT_ALIASES) == "qwen/qwen3.7-max"
    assert resolve_model("gef", DEFAULT_ALIASES) == "google/gemini-3.5-flash"
    assert resolve_model("ge25lite", DEFAULT_ALIASES) == "google/gemini-2.5-flash-lite"
    # M28: current OpenAI small models are GPT-5.4 mini/nano
    assert resolve_model("gptmini", DEFAULT_ALIASES) == "openai/gpt-5.4-mini"
    assert resolve_model("gptnano", DEFAULT_ALIASES) == "openai/gpt-5.4-nano"


def test_aliases_apr_2026_still_current():
    """M22 aliases that remain current in June 2026."""
    assert resolve_model("gpt", DEFAULT_ALIASES) == "openai/gpt-5.5"
    assert resolve_model("gptpro", DEFAULT_ALIASES) == "openai/gpt-5.5-pro"
    assert resolve_model("dsf", DEFAULT_ALIASES) == "deepseek/deepseek-v4-flash"
    assert resolve_model("dsp", DEFAULT_ALIASES) == "deepseek/deepseek-v4-pro"
    assert resolve_model("glm", DEFAULT_ALIASES) == "z-ai/glm-5.1"
    assert resolve_model("mm", DEFAULT_ALIASES) == "minimax/minimax-m2.7"
    assert resolve_model("kimi", DEFAULT_ALIASES) == "moonshotai/kimi-k2.6"


def test_retained_aliases():
    """Aliases kept from the previous catalog (still current in apr 2026)."""
    assert resolve_model("cls", DEFAULT_ALIASES) == "anthropic/claude-sonnet-4.6"
    assert resolve_model("clh", DEFAULT_ALIASES) == "anthropic/claude-haiku-4.5"
    assert resolve_model("gel", DEFAULT_ALIASES) == "google/gemini-3.1-flash-lite-preview"
    assert resolve_model("gep", DEFAULT_ALIASES) == "google/gemini-3.1-pro-preview"


def test_retired_aliases_passthrough():
    """Every retired alias must not resolve — it passes through unchanged."""
    for alias in RETIRED_ALIASES:
        assert resolve_model(alias, DEFAULT_ALIASES) == alias, f"{alias} should not resolve"


def test_retired_disjoint_from_defaults():
    """A retired alias key must never also be a current default."""
    assert RETIRED_ALIASES.isdisjoint(DEFAULT_ALIASES)


def test_alias_renames_point_from_retired_to_current_aliases():
    assert set(ALIAS_RENAMES).issubset(RETIRED_ALIASES)
    assert set(ALIAS_RENAMES.values()).issubset(DEFAULT_ALIASES)


def test_m28_openai_old_small_models_retired():
    """M28: GPT-5 mini/nano and o4-mini are retired in favour of GPT-5.4 small."""
    for alias in ("gpt5mini", "gpt5nano", "o4m"):
        assert alias in RETIRED_ALIASES
        assert resolve_model(alias, DEFAULT_ALIASES) == alias


def test_all_default_aliases_resolve():
    for alias, full_name in DEFAULT_ALIASES.items():
        assert resolve_model(alias, DEFAULT_ALIASES) == full_name
