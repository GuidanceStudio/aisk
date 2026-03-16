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
    """Create ~/.aisk/ with default files. Returns list of actions taken."""
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
