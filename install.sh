#!/usr/bin/env bash
set -euo pipefail

REPO="git+ssh://git@github.com/Ymx1ZQ/aisk.git"

# Install uv if missing
if ! command -v uv &>/dev/null; then
    echo "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install or upgrade
if uv tool list 2>/dev/null | grep -q '^aisk '; then
    echo "aisk found — upgrading..."
    uv tool install --force --upgrade "$REPO"
else
    echo "Installing aisk..."
    uv tool install "$REPO"
fi

echo ""
echo "Running setup wizard..."
echo ""
aisk init

echo ""
echo "Done! Run 'aisk --version' to verify."
