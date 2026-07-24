# Setup Guide

Step-by-step instructions to install and configure AutoGodot on Ubuntu.

## Prerequisites

### Required

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.10+ | MCP server runtime |
| **Godot** | 4.7 | Game engine (for running/testing games) |

### Optional (for Claude Desktop integration)

| Software | Purpose |
|----------|---------|
| **Claude Desktop** | AI client that connects to the MCP server |

## Step 1: Install Python 3.10+

```bash
# Check if Python 3.10+ is installed
python3 --version

# If not installed:
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

## Step 2: Install Godot 4.7

```bash
# Option A: Download from official site
# https://godotengine.org/download/linux
# Extract and place in /usr/local/bin/godot4

# Option B: Flatpak
flatpak install flathub org.godotengine.Godot

# Option C: Snap
sudo snap install godot-4

# Verify installation
godot4 --version
```

## Step 3: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/autogodot.git
cd autogodot
```

## Step 4: Run the Setup Script

```bash
chmod +x scripts/setup_and_run.sh
./scripts/setup_and_run.sh
```

The script will:

1. **Verify Python 3.10+** — Checks `python3` and `pip` are available
2. **Verify Godot 4.7** — Searches common installation paths
3. **Create `.venv/`** — Isolated Python environment with all dependencies
4. **Install dependencies** — `mcp`, `pydantic`, `mss`, `Pillow`, etc.
5. **Inject Claude Desktop config** — Adds the MCP server to `~/.config/Claude/claude_desktop_config.json`
6. **Start the MCP server** — Launches via stdio transport

## Step 5: Verify in Claude Desktop

1. Open Claude Desktop
2. Start a new conversation
3. Ask: "What tools do you have available for Godot?"
4. Claude should list the three tools: `write_game_file`, `run_godot_test`, `capture_game_screen`

## Manual Setup (Without the Script)

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the MCP server directly
python core/mcp_server.py
```

For Claude Desktop, manually add this to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "autogodot": {
      "command": "/absolute/path/to/autogodot/.venv/bin/python",
      "args": ["/absolute/path/to/autogodot/core/mcp_server.py"],
      "env": {
        "GODOT_PATH": "godot4",
        "GODOT_PROJECT": "/path/to/your/godot/project"
      }
    }
  }
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GODOT_PATH` | `godot4` | Path to Godot 4.7 executable |
| `GODOT_PROJECT` | `.` (current directory) | Path to the Godot project directory |
| `SKIP_CLAUDE_CFG` | `0` | Set to `1` to skip Claude Desktop config injection |
| `CLAUDE_CFG_PATH` | `~/.config/Claude/claude_desktop_config.json` | Override Claude Desktop config path |

### Finding Your Godot Path

```bash
# Check common locations
which godot4
which godot

# If installed via Flatpak
flatpak info --show-location org.godotengine.Godot

# If installed via Snap
snap info godot-4
```

### Setting GODOT_PROJECT

The `GODOT_PROJECT` should point to a directory containing `project.godot`:

```bash
# Example
export GODOT_PROJECT="/home/user/games/my-platformer"

# Or pass it to the setup script
GODOT_PROJECT="/home/user/games/my-platformer" ./scripts/setup_and_run.sh
```

## Troubleshooting

### "Python 3.10+ is required but not found"

```bash
# Check what Python versions are available
ls /usr/bin/python*

# Install Python 3.10
sudo apt install python3.10 python3.10-venv
```

### "Godot 4.7 not found"

```bash
# Check if Godot is installed
which godot4 || which godot

# If you know where it is, set the path
GODOT_PATH="/path/to/godot4" ./scripts/setup_and_run.sh
```

### "Claude Desktop config not found"

This is normal if Claude Desktop isn't installed. The MCP server still works — you just need to configure your MCP client manually. See the [Manual Setup](#manual-setup-without-the-script) section.

### MCP Server Starts But Tools Don't Appear in Claude Desktop

1. Check the config file exists: `cat ~/.config/Claude/claude_desktop_config.json`
2. Verify the `autogodot` entry is present
3. Restart Claude Desktop after config changes
4. Check Claude Desktop logs for MCP connection errors

### "ModuleNotFoundError: No module named 'mcp'"

The virtual environment isn't activated or dependencies aren't installed:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Testing the Installation

Create a simple test script to verify everything works:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the MCP server (it will wait for stdin input)
python core/mcp_server.py

# Send a test JSON-RPC request (press Ctrl+D to end)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python core/mcp_server.py
```

You should see a JSON response listing the eight tools.
