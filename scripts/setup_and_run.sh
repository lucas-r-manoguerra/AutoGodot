#!/usr/bin/env bash
# =============================================================================
# AutoGodot — One-click setup & run for Ubuntu
# =============================================================================
# This script:
#   1. Verifies system prerequisites (Python 3.10+, pip, Godot 4.x)
#   2. Creates an isolated Python virtual environment (.venv)
#   3. Installs all Python dependencies from requirements.txt
#   4. Injects MCP server configuration into Claude Desktop's config file
#   5. Launches the MCP server via stdio transport
#
# Usage:
#   chmod +x scripts/setup_and_run.sh
#   ./scripts/setup_and_run.sh
#
# Environment variables (all optional):
#   GODOT_PATH       — Explicit path to the Godot 4.x executable
#   GODOT_PROJECT    — Path to the Godot project directory (default:cwd)
#   SKIP_CLAUDE_CFG  — Set to 1 to skip Claude Desktop config injection
#   CLAUDE_CFG_PATH  — Override the Claude Desktop config file path
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${PROJECT_ROOT}/.venv"
REQUIREMENTS="${PROJECT_ROOT}/requirements.txt"
MCP_SERVER_ENTRY="${PROJECT_ROOT}/core/mcp_server.py"

# Claude Desktop config path (Ubuntu default)
CLAUDE_CFG_PATH="${CLAUDE_CFG_PATH:-${HOME}/.config/Claude/claude_desktop_config.json}"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_fatal()   { log_error "$@"; exit 1; }

# ---------------------------------------------------------------------------
# 1. System Prerequisites
# ---------------------------------------------------------------------------
log_info "=== AutoGodot Setup ==="
echo ""

# --- Python ---
log_info "Checking Python..."
PYTHON_CMD=""

# Try python3 first, then python
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        version_output="$("$candidate" --version 2>&1)"
        version_number="$(echo "$version_output" | grep -oP '\d+\.\d+')"
        major="$(echo "$version_number" | cut -d. -f1)"
        minor="$(echo "$version_number" | cut -d. -f2)"

        if [[ "$major" -ge 3 ]] && [[ "$minor" -ge 10 ]]; then
            PYTHON_CMD="$candidate"
            log_ok "Python ${version_number} found at $(command -v "$candidate")"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    log_fatal "Python 3.10+ is required but not found. Install with: sudo apt install python3.10 python3.10-venv"
fi

# --- pip ---
log_info "Checking pip..."
if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then
    log_warn "pip not found. Attempting to install..."
    "$PYTHON_CMD" -m ensurepip --upgrade 2>/dev/null || {
        log_fatal "pip is not available. Install manually: sudo apt install python3-pip"
    }
fi
log_ok "pip available"

# --- Godot ---
log_info "Checking Godot 4.x..."
GODOT_EXECUTABLE=""

# Priority: env var > common paths > PATH search
if [[ -n "${GODOT_PATH:-}" ]] && [[ -x "$GODOT_PATH" ]]; then
    GODOT_EXECUTABLE="$GODOT_PATH"
elif command -v godot4 &>/dev/null; then
    GODOT_EXECUTABLE="$(command -v godot4)"
elif command -v godot &>/dev/null; then
    # Verify it's Godot 4.x (Godot 3 uses "godot", 4 uses "godot4" on some installs)
    godot_version_output="$(godot --version 2>&1 || true)"
    if echo "$godot_version_output" | grep -qP '^4\.'; then
        GODOT_EXECUTABLE="$(command -v godot)"
    fi
else
    # Search common installation paths
    for path_candidate in \
        /usr/bin/godot4 \
        /usr/local/bin/godot4 \
        /opt/godot/godot4 \
        "${HOME}/.local/bin/godot4" \
        "${HOME}/Applications/Godot4" \
        /snap/bin/godot \
        /usr/bin/godot; do
        if [[ -x "$path_candidate" ]]; then
            GODOT_EXECUTABLE="$path_candidate"
            break
        fi
    done
fi

if [[ -z "$GODOT_EXECUTABLE" ]]; then
    log_warn "Godot 4.x not found. The MCP server will start but Godot tools will fail."
    log_warn "Install Godot 4.x: https://godotengine.org/download/linux"
    GODOT_EXECUTABLE="godot4"  # Fallback — let it fail at runtime with a clear error
else
    log_ok "Godot found at ${GODOT_EXECUTABLE}"
fi

echo ""

# ---------------------------------------------------------------------------
# 2. Virtual Environment
# ---------------------------------------------------------------------------
log_info "Setting up Python virtual environment..."

if [[ -d "$VENV_DIR" ]]; then
    log_warn "Existing .venv found — recreating..."
    rm -rf "$VENV_DIR"
fi

"$PYTHON_CMD" -m venv "$VENV_DIR"
log_ok "Virtual environment created at ${VENV_DIR}"

# Activate
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
log_ok "Virtual environment activated"

# Upgrade pip silently
pip install --quiet --upgrade pip setuptools wheel 2>/dev/null
log_ok "pip upgraded"

# ---------------------------------------------------------------------------
# 3. Dependencies
# ---------------------------------------------------------------------------
log_info "Installing Python dependencies..."

if [[ ! -f "$REQUIREMENTS" ]]; then
    log_fatal "requirements.txt not found at ${REQUIREMENTS}"
fi

pip install --quiet -r "$REQUIREMENTS"
log_ok "Dependencies installed"

echo ""

# ---------------------------------------------------------------------------
# 4. Claude Desktop Configuration Injection
# ---------------------------------------------------------------------------
if [[ "${SKIP_CLAUDE_CFG:-0}" == "1" ]]; then
    log_info "Skipping Claude Desktop config injection (SKIP_CLAUDE_CFG=1)"
else
    log_info "Configuring Claude Desktop MCP integration..."

    CLAUDE_CFG_DIR="$(dirname "$CLAUDE_CFG_PATH")"

    # Create directory if it doesn't exist
    if [[ ! -d "$CLAUDE_CFG_DIR" ]]; then
        mkdir -p "$CLAUDE_CFG_DIR"
        log_info "Created Claude config directory: ${CLAUDE_CFG_DIR}"
    fi

    # The MCP server command that Claude Desktop will invoke
    MCP_CMD="${VENV_DIR}/bin/python"
    MCP_ARGS="${MCP_SERVER_ENTRY}"

    # Build the JSON config block for our server
    # Using printf to avoid jq dependency
    MCP_CONFIG_BLOCK=$(cat <<JSONEOF
{
  "mcpServers": {
    "autogodot": {
      "command": "${MCP_CMD}",
      "args": ["${MCP_ARGS}"],
      "env": {
        "GODOT_PATH": "${GODOT_EXECUTABLE}",
        "GODOT_PROJECT": "${GODOT_PROJECT:-$(dirname "$SCRIPT_DIR")}"
      }
    }
  }
}
JSONEOF
)

    if [[ ! -f "$CLAUDE_CFG_PATH" ]]; then
        # No config file exists — create it with our entry
        echo "$MCP_CONFIG_BLOCK" > "$CLAUDE_CFG_PATH"
        log_ok "Created Claude Desktop config with autogodot server"
    else
        # Config file exists — check if our server is already registered
        if grep -q '"autogodot"' "$CLAUDE_CFG_PATH" 2>/dev/null; then
            log_ok "autogodot already registered in Claude Desktop config"
        else
            # Merge our entry into existing config
            # Try python json manipulation (available since we have python)
            "$PYTHON_CMD" -c "
import json, sys

config_path = '${CLAUDE_CFG_PATH}'
with open(config_path, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['autogodot'] = {
    'command': '${MCP_CMD}',
    'args': ['${MCP_ARGS}'],
    'env': {
        'GODOT_PATH': '${GODOT_EXECUTABLE}',
        'GODOT_PROJECT': '${GODOT_PROJECT:-$(dirname "$SCRIPT_DIR")}'
    }
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print('Merged autogodot into existing config')
"
            log_ok "Merged autogodot into existing Claude Desktop config"
        fi
    fi
fi

echo ""

# ---------------------------------------------------------------------------
# 5. Launch MCP Server
# ---------------------------------------------------------------------------
log_info "=== Starting AutoGodot MCP Server ==="
log_info "Transport: stdio"
log_info "Server:   ${MCP_SERVER_ENTRY}"
log_info "Godot:    ${GODOT_EXECUTABLE}"
echo ""
log_info "Press Ctrl+C to stop the server"
echo ""

# Export env vars for the server process
export GODOT_PATH="$GODOT_EXECUTABLE"
export GODOT_PROJECT="${GODOT_PROJECT:-$(dirname "$SCRIPT_DIR")}"

exec "$VENV_DIR/bin/python" "$MCP_SERVER_ENTRY"
