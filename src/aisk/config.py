from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

CONFIG_DIR = Path.home() / ".aisk"
CONFIG_FILE = CONFIG_DIR / "conf.toml"
ENV_FILE = CONFIG_DIR / ".env"

DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_ALIASES: dict[str, str] = {
    # Google Gemini
    "ge31pro": "google/gemini-3.1-pro-preview",
    "ge3flash": "google/gemini-2.5-flash-preview",
    "ge25flash": "google/gemini-2.5-flash-preview",
    "ge25lite": "google/gemini-2.5-flash-lite-preview",
    # OpenAI
    "gpt52": "openai/gpt-5.2",
    "gpt51": "openai/gpt-5.1",
    "gpt5": "openai/gpt-5",
    "gpt5mini": "openai/gpt-5-mini",
    "gpt5nano": "openai/gpt-5-nano",
    "o4m": "openai/o4-mini",
    # Anthropic
    "clo46": "anthropic/claude-opus-4",
    "cls46": "anthropic/claude-sonnet-4",
    # DeepSeek
    "dsv32": "deepseek/deepseek-chat-v3-0324",
    "dsr1": "deepseek/deepseek-r1",
    # Qwen
    "qwen35p": "qwen/qwen3.5-coder-plus",
    "qwen35": "qwen/qwen3.5-coder",
    # Perplexity
    "s": "perplexity/sonar",
    "sps": "perplexity/sonar-pro-search",
    # Other
    "m25": "minimax/minimax-m1-80k",
    "glm5": "zhipu/glm-5-plus",
    "k25": "moonshotai/kimi-k2.5",
    "mistral": "mistralai/mistral-large-2411",
    "l4scout": "meta-llama/llama-4-scout",
    "l4mav": "meta-llama/llama-4-maverick",
}

DEFAULT_CONF_TOML = """\
[api]
endpoint = "https://openrouter.ai/api/v1/chat/completions"

[aliases]
# Google Gemini
ge31pro = "google/gemini-3.1-pro-preview"
ge3flash = "google/gemini-2.5-flash-preview"
ge25flash = "google/gemini-2.5-flash-preview"
ge25lite = "google/gemini-2.5-flash-lite-preview"

# OpenAI
gpt52 = "openai/gpt-5.2"
gpt51 = "openai/gpt-5.1"
gpt5 = "openai/gpt-5"
gpt5mini = "openai/gpt-5-mini"
gpt5nano = "openai/gpt-5-nano"
o4m = "openai/o4-mini"

# Anthropic
clo46 = "anthropic/claude-opus-4"
cls46 = "anthropic/claude-sonnet-4"

# DeepSeek
dsv32 = "deepseek/deepseek-chat-v3-0324"
dsr1 = "deepseek/deepseek-r1"

# Qwen
qwen35p = "qwen/qwen3.5-coder-plus"
qwen35 = "qwen/qwen3.5-coder"

# Perplexity
s = "perplexity/sonar"
sps = "perplexity/sonar-pro-search"

# Other
m25 = "minimax/minimax-m1-80k"
glm5 = "zhipu/glm-5-plus"
k25 = "moonshotai/kimi-k2.5"
mistral = "mistralai/mistral-large-2411"
l4scout = "meta-llama/llama-4-scout"
l4mav = "meta-llama/llama-4-maverick"
"""

DEFAULT_ENV = """\
AISK_API_KEY=
"""


@dataclass
class Config:
    endpoint: str = DEFAULT_ENDPOINT
    api_key: str = ""
    aliases: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_ALIASES))


def load_config() -> Config:
    """Load config from ~/.aisk/conf.toml and ~/.aisk/.env."""
    # Load .env first so AISK_API_KEY is available
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)

    cfg = Config()

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        api = data.get("api", {})
        if "endpoint" in api:
            cfg.endpoint = api["endpoint"]
        aliases = data.get("aliases", {})
        if aliases:
            cfg.aliases.update(aliases)

    cfg.api_key = os.environ.get("AISK_API_KEY", "")
    return cfg


def init_config() -> list[str]:
    """Create ~/.aisk/ with default files (non-interactive). Returns list of actions taken."""
    actions: list[str] = []
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        actions.append(f"Skipped {CONFIG_FILE} (already exists)")
    else:
        CONFIG_FILE.write_text(DEFAULT_CONF_TOML)
        actions.append(f"Created {CONFIG_FILE}")

    if ENV_FILE.exists():
        actions.append(f"Skipped {ENV_FILE} (already exists)")
    else:
        ENV_FILE.write_text(DEFAULT_ENV)
        actions.append(f"Created {ENV_FILE}")

    return actions


def _mask_key(key: str) -> str:
    """Mask an API key for display, showing first 6 and last 4 chars."""
    if len(key) <= 10:
        return "****"
    return f"{key[:6]}...{key[-4:]}"


def _read_existing_key() -> str:
    """Read the current AISK_API_KEY from the .env file, if any."""
    if not ENV_FILE.exists():
        return ""
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("AISK_API_KEY=") and not line.startswith("#"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _write_env(api_key: str) -> None:
    """Write the .env file with the given API key."""
    ENV_FILE.write_text(f"AISK_API_KEY={api_key}\n")


def _write_conf(endpoint: str) -> None:
    """Write conf.toml with the given endpoint and default aliases."""
    content = DEFAULT_CONF_TOML
    if endpoint != DEFAULT_ENDPOINT:
        content = content.replace(
            f'endpoint = "{DEFAULT_ENDPOINT}"',
            f'endpoint = "{endpoint}"',
        )
    CONFIG_FILE.write_text(content)


def interactive_init(
    input_fn=None,
    print_fn=None,
) -> None:
    """Interactive setup wizard for ~/.aisk/ configuration.

    Args:
        input_fn: Callable for user input (default: builtins.input).
        print_fn: Callable for output (default: builtins.print).
    """
    if input_fn is None:
        input_fn = input
    if print_fn is None:
        print_fn = print

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # --- conf.toml ---
    if CONFIG_FILE.exists():
        print_fn(f"\n  conf.toml already exists at {CONFIG_FILE}")
        overwrite = input_fn("  Overwrite? [y/N] ").strip().lower()
        if overwrite in ("y", "yes"):
            endpoint = input_fn(
                f"  Endpoint [{DEFAULT_ENDPOINT}]: "
            ).strip()
            if not endpoint:
                endpoint = DEFAULT_ENDPOINT
            _write_conf(endpoint)
            print_fn(f"  ✓ Wrote {CONFIG_FILE}")
        else:
            print_fn("  Skipped conf.toml")
    else:
        endpoint = input_fn(
            f"  Endpoint [{DEFAULT_ENDPOINT}]: "
        ).strip()
        if not endpoint:
            endpoint = DEFAULT_ENDPOINT
        _write_conf(endpoint)
        print_fn(f"  ✓ Created {CONFIG_FILE}")

    # --- .env ---
    existing_key = _read_existing_key()
    if existing_key:
        print_fn(f"\n  API key already set: {_mask_key(existing_key)}")
        overwrite = input_fn("  Overwrite? [y/N] ").strip().lower()
        if overwrite in ("y", "yes"):
            new_key = input_fn("  AISK_API_KEY: ").strip()
            if new_key:
                _write_env(new_key)
                print_fn("  ✓ API key updated")
            else:
                print_fn("  Empty key — kept existing")
        else:
            print_fn("  Skipped .env")
    else:
        new_key = input_fn("  AISK_API_KEY: ").strip()
        if new_key:
            _write_env(new_key)
            print_fn(f"  ✓ Created {ENV_FILE}")
        else:
            _write_env("")
            print_fn(f"  ✓ Created {ENV_FILE} (empty key — edit later)")

    print_fn("\n  ✓ Configuration saved to ~/.aisk/")
