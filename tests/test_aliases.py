from aisk.aliases import resolve_model
from aisk.config import ALIAS_RENAMES, DEFAULT_ALIASES, RETIRED_ALIASES


def test_known_alias():
    assert resolve_model("gel", DEFAULT_ALIASES) == "google/gemini-3.5-flash-lite"


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
    """M24/M28: quel che regge ancora del refresh di giugno 2026.

    clo, qwen e gef sono passati a M52; qui restano solo gli alias che quel
    refresh ha fissato e che il catalogo di settembre 2026 non ha superato.
    """
    assert resolve_model("ge25lite", DEFAULT_ALIASES) == "google/gemini-2.5-flash-lite"
    # M28: current OpenAI small models are GPT-5.4 mini/nano
    assert resolve_model("gptmini", DEFAULT_ALIASES) == "openai/gpt-5.4-mini"
    assert resolve_model("gptnano", DEFAULT_ALIASES) == "openai/gpt-5.4-nano"


def test_dsp_alias_points_to_v4_pro_0813_ga():
    """M49: dsp moved from the apr-2026 v4-pro preview to the aug-2026 GA (0813)."""
    assert resolve_model("dsp", DEFAULT_ALIASES) == "deepseek/deepseek-v4-pro-0813"


def test_retained_aliases():
    """Alias mai superati: clh è l'ultimo Haiku, gep l'ultimo Gemini Pro (set 2026)."""
    assert resolve_model("clh", DEFAULT_ALIASES) == "anthropic/claude-haiku-4.5"
    assert resolve_model("gep", DEFAULT_ALIASES) == "google/gemini-3.1-pro-preview"


def test_aliases_sep_2026_refresh():
    """M52: ogni slug verificato contro /api/v1/models il 2026-09-18."""
    assert resolve_model("dsf", DEFAULT_ALIASES) == "deepseek/deepseek-v4.1-flash"
    assert resolve_model("clo", DEFAULT_ALIASES) == "anthropic/claude-opus-5"
    assert resolve_model("cls", DEFAULT_ALIASES) == "anthropic/claude-sonnet-5"
    assert resolve_model("gef", DEFAULT_ALIASES) == "google/gemini-3.8-flash"
    assert resolve_model("gel", DEFAULT_ALIASES) == "google/gemini-3.5-flash-lite"
    assert resolve_model("qwen", DEFAULT_ALIASES) == "qwen/qwen3.8-max-0902"
    assert resolve_model("mm", DEFAULT_ALIASES) == "minimax/minimax-m3"
    assert resolve_model("glm", DEFAULT_ALIASES) == "z-ai/glm-5.3"
    assert resolve_model("kimi", DEFAULT_ALIASES) == "moonshotai/kimi-k3"
    # gpt/gptpro tengono lo slot flagship: Sol e' il flagship della serie 5.6,
    # Terra il bilanciato e Luna l'economico (descrizioni del catalogo OpenRouter).
    assert resolve_model("gpt", DEFAULT_ALIASES) == "openai/gpt-5.6-sol"
    assert resolve_model("gptpro", DEFAULT_ALIASES) == "openai/gpt-5.6-sol-pro"


def test_m52_mistral_repointed_off_delisted_model():
    """M52: mistral-large-2512 è stato delistato (resta solo la variante :batch)."""
    assert resolve_model("mistral", DEFAULT_ALIASES) == "mistralai/mistral-medium-3-5"


def test_m52_llama_groq_aliases_retired():
    """M52: Groq non è più fra i provider di llama-4 su OpenRouter, il pin :groq falliva."""
    for alias in ("lscout", "lmav", "l4scout", "l4mav"):
        assert alias in RETIRED_ALIASES
        assert resolve_model(alias, DEFAULT_ALIASES) == alias


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
