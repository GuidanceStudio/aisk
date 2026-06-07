#!/usr/bin/env bash
set -euo pipefail

REPO="git+https://github.com/GuidanceStudio/aisk.git"

INSTALL_TARGET="$REPO"
INSTALL_SOURCE="GitHub"
SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
if [[ -n "$SCRIPT_SOURCE" && -f "$SCRIPT_SOURCE" ]]; then
    SCRIPT_DIR="$(cd -- "$(dirname -- "$SCRIPT_SOURCE")" && pwd -P)"
    if [[ -f "$SCRIPT_DIR/pyproject.toml" && -d "$SCRIPT_DIR/src/aisk" ]]; then
        INSTALL_TARGET="$SCRIPT_DIR"
        INSTALL_SOURCE="local checkout"
    fi
fi

# Colors
BLUE='\033[38;5;33m'
CYAN='\033[36m'
GREEN='\033[32m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'
SEP="${BLUE}──────────────────────────────────────────────────────────────────────────────────────────────${RESET}"

echo ""
echo -e "${SEP}"
echo -e "  ${BOLD}aisk${RESET} ${DIM}— installer${RESET}"
echo -e "${SEP}"
echo ""

# Install uv if missing
if ! command -v uv &>/dev/null; then
    echo -e "  ${DIM}uv not found — installing...${RESET}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo ""
fi

# Install or upgrade
if uv tool list 2>/dev/null | grep -q '^aisk '; then
    echo -e "  ${CYAN}[1/3]${RESET} Upgrading aisk..."
    echo -e "  ${DIM}source: ${INSTALL_SOURCE} (${INSTALL_TARGET})${RESET}"
    uv tool install --force --upgrade "$INSTALL_TARGET"
else
    echo -e "  ${CYAN}[1/3]${RESET} Installing aisk..."
    echo -e "  ${DIM}source: ${INSTALL_SOURCE} (${INSTALL_TARGET})${RESET}"
    uv tool install "$INSTALL_TARGET"
fi

echo ""
echo -e "  ${CYAN}[2/3]${RESET} Setup"
echo ""
aisk init

echo ""
echo -e "  ${CYAN}[3/3]${RESET} Shell completions"
echo -e "  ${DIM}$(aisk completions install)${RESET}"

echo ""

# Detect shell rc file for the hint
if [[ "${SHELL:-}" == */zsh ]]; then
    _RC_FILE="$HOME/.zshrc"
    _RC="~/.zshrc"
else
    _RC_FILE="$HOME/.bashrc"
    _RC="~/.bashrc"
fi

# Warn about old a+ask functions
if [[ -f "$_RC_FILE" ]] && grep -q 'a+ask' "$_RC_FILE"; then
    echo -e "  ${BOLD}Note:${RESET} Found old ${DIM}a+ask${RESET} functions in ${DIM}$_RC${RESET}"
    echo -e "  You can remove them — aisk now generates shortcuts from ${DIM}~/.aisk/conf.toml${RESET}"
    echo -e "  Run ${BOLD}aisk shortcuts${RESET} to see the generated functions."
    echo ""
fi

echo -e "${SEP}"
echo -e "  ${GREEN}✓${RESET} All done! Run ${BOLD}source ${_RC}${RESET} to activate completions,"
echo -e "    then ${BOLD}aisk --version${RESET} to verify."
echo -e "${SEP}"
echo ""
