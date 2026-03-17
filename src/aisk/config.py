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
    "ge31lite": "google/gemini-3.1-flash-lite-preview",
    "ge25flash": "google/gemini-2.5-flash",
    # OpenAI
    "gpt54": "openai/gpt-5.4",
    "gpt5mini": "openai/gpt-5-mini",
    "gpt5nano": "openai/gpt-5-nano",
    "o4m": "openai/o4-mini",
    # Anthropic
    "clo46": "anthropic/claude-opus-4.6",
    "cls46": "anthropic/claude-sonnet-4.6",
    "clh45": "anthropic/claude-haiku-4.5",
    # DeepSeek
    "dsv32": "deepseek/deepseek-v3.2",
    "dsr1": "deepseek/deepseek-r1",
    # Qwen
    "qwen35p": "qwen/qwen3.5-plus-02-15",
    "qwen35": "qwen/qwen3.5-397b-a17b",
    # Perplexity
    "s": "perplexity/sonar",
    "sps": "perplexity/sonar-pro-search",
    # Other
    "m25": "minimax/minimax-m2.5",
    "glm5": "z-ai/glm-5",
    "mistral": "mistralai/mistral-large-2512",
    "l4scout": "meta-llama/llama-4-scout:groq",
    "l4mav": "meta-llama/llama-4-maverick:groq",
}

DEFAULT_CONF_TOML = """\
[api]
endpoint = "https://openrouter.ai/api/v1/chat/completions"

[aliases]
# Google Gemini
ge31pro = "google/gemini-3.1-pro-preview"
ge31lite = "google/gemini-3.1-flash-lite-preview"
ge25flash = "google/gemini-2.5-flash"

# OpenAI
gpt54 = "openai/gpt-5.4"
gpt5mini = "openai/gpt-5-mini"
gpt5nano = "openai/gpt-5-nano"
o4m = "openai/o4-mini"

# Anthropic
clo46 = "anthropic/claude-opus-4.6"
cls46 = "anthropic/claude-sonnet-4.6"
clh45 = "anthropic/claude-haiku-4.5"

# DeepSeek
dsv32 = "deepseek/deepseek-v3.2"
dsr1 = "deepseek/deepseek-r1"

# Qwen
qwen35p = "qwen/qwen3.5-plus-02-15"
qwen35 = "qwen/qwen3.5-397b-a17b"

# Perplexity
s = "perplexity/sonar"
sps = "perplexity/sonar-pro-search"

# Other
m25 = "minimax/minimax-m2.5"
glm5 = "z-ai/glm-5"
mistral = "mistralai/mistral-large-2512"
l4scout = "meta-llama/llama-4-scout:groq"
l4mav = "meta-llama/llama-4-maverick:groq"
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


class ConfigError(Exception):
    """Raised when config cannot be loaded and auto-init is not possible."""


def ensure_config() -> Config:
    """Load config, auto-launching the setup wizard if needed.

    - If config/key is missing and stdin is a TTY → run interactive_init(), then reload.
    - If config/key is missing and stdin is NOT a TTY → raise ConfigError.
    - Otherwise → return the loaded Config.
    """
    cfg = load_config()
    if cfg.api_key:
        return cfg

    # Config or API key is missing — try auto-init
    if sys.stdin.isatty():
        print("\n  First run detected — launching setup wizard...\n")
        interactive_init(auto=True)
        # Reload after wizard
        cfg = load_config()
        if cfg.api_key:
            return cfg

    raise ConfigError("AISK_API_KEY not set. Run 'aisk init' and edit ~/.aisk/.env")


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
    *,
    auto: bool = False,
) -> None:
    """Interactive setup wizard for ~/.aisk/ configuration.

    Args:
        input_fn: Callable for user input (default: builtins.input).
        print_fn: Callable for output (default: builtins.print).
        auto: When True (called from ensure_config), skip overwrite prompts
              and only ask for what's missing.
    """
    if input_fn is None:
        input_fn = input
    if print_fn is None:
        print_fn = print

    # ANSI styling
    _B = "\033[38;5;33m"   # blue
    _C = "\033[36m"         # cyan
    _G = "\033[32m"         # green
    _D = "\033[2m"          # dim
    _BD = "\033[1m"         # bold
    _Y = "\033[33m"         # yellow
    _R = "\033[0m"          # reset
    _SEP = f"{_B}{'─' * 60}{_R}"

    print_fn("")
    print_fn(_SEP)
    print_fn(f"  {_BD}aisk{_R} {_D}— setup{_R}")
    print_fn(_SEP)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # --- conf.toml ---
    print_fn(f"\n  {_C}{_BD}Endpoint{_R}")

    if CONFIG_FILE.exists():
        if auto:
            print_fn(f"  {_D}conf.toml exists — kept{_R}")
        else:
            print_fn(f"  {_D}conf.toml already exists at {CONFIG_FILE}{_R}")
            overwrite = input_fn(f"  {_Y}Overwrite? [y/N]{_R} ").strip().lower()
            if overwrite in ("y", "yes"):
                endpoint = input_fn(
                    f"  Endpoint [{_D}{DEFAULT_ENDPOINT}{_R}]: "
                ).strip()
                if not endpoint:
                    endpoint = DEFAULT_ENDPOINT
                _write_conf(endpoint)
                print_fn(f"  {_G}✓{_R} Wrote {_D}{CONFIG_FILE}{_R}")
            else:
                print_fn(f"  {_D}skipped{_R}")
    else:
        endpoint = input_fn(
            f"  URL [{_D}{DEFAULT_ENDPOINT}{_R}]: "
        ).strip()
        if not endpoint:
            endpoint = DEFAULT_ENDPOINT
        _write_conf(endpoint)
        print_fn(f"  {_G}✓{_R} {endpoint}")

    # --- .env ---
    print_fn(f"\n  {_C}{_BD}API Key{_R}")

    existing_key = _read_existing_key()
    if existing_key:
        if auto:
            print_fn(f"  {_D}key exists — kept{_R}")
        else:
            print_fn(f"  {_D}current: {_mask_key(existing_key)}{_R}")
            overwrite = input_fn(f"  {_Y}Overwrite? [y/N]{_R} ").strip().lower()
            if overwrite in ("y", "yes"):
                new_key = input_fn(f"  AISK_API_KEY: ").strip()
                if new_key:
                    _write_env(new_key)
                    print_fn(f"  {_G}✓{_R} updated")
                else:
                    print_fn(f"  {_D}empty — kept existing{_R}")
            else:
                print_fn(f"  {_D}skipped{_R}")
    else:
        new_key = input_fn(f"  AISK_API_KEY: ").strip()
        if new_key:
            _write_env(new_key)
            print_fn(f"  {_G}✓{_R} saved")
        else:
            _write_env("")
            print_fn(f"  {_Y}!{_R} empty — edit {_D}~/.aisk/.env{_R} later")

    print_fn("")
    print_fn(_SEP)
    print_fn(f"  {_G}✓{_R} Config saved to {_BD}~/.aisk/{_R}")
    print_fn(_SEP)
    print_fn("")
