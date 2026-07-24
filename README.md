# AutoGodot

Autonomous game development framework that lets AI agents program, design scenes, and run visual QA on Godot 4.7 projects — all through the Model Context Protocol (MCP).

## What It Does

An AI agent (Claude Desktop, VS Code, or any MCP-compatible client) can:

- **Write game files** — Create/edit GDScript (`.gd`) and scene (`.tscn`) files directly
- **Run Godot tests** — Launch the project, capture console output, detect errors
- **Capture screenshots** — Take visual QA screenshots of the running game for design verification

## Quick Start (Ubuntu)

```bash
git clone https://github.com/YOUR_USERNAME/autogodot.git
cd autogodot
chmod +x scripts/setup_and_run.sh
./scripts/setup_and_run.sh
```

The setup script handles everything:
1. Verifies Python 3.10+ and Godot 4.7 are installed
2. Creates an isolated virtual environment
3. Installs all dependencies
4. Injects MCP server config into Claude Desktop (auto-detected)
5. Starts the MCP server

## Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python core/mcp_server.py
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `write_game_file` | Create or overwrite `.gd`, `.tscn`, `.tres` files in the project |
| `run_godot_test` | Launch Godot with a scene, capture stdout/stderr, enforce timeout |
| `capture_game_screen` | Screenshot the running game window, return Base64 JPEG |
| `read_scene` | Parse a .tscn into structured JSON |
| `create_scene` | Build a .tscn from a JSON definition |
| `modify_scene` | Apply surgical operations to an existing .tscn |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `GODOT_PATH` | `godot4` | Path to Godot 4.7 executable |
| `GODOT_PROJECT` | `.` (cwd) | Path to the Godot project directory |
| `SKIP_CLAUDE_CFG` | `0` | Set to `1` to skip Claude Desktop config injection |

## Project Structure

```
autogodot/
├── config/                  # MCP client config templates
├── core/
│   ├── __init__.py
│   ├── mcp_server.py        # MCP server (stdio transport)
│   ├── godot_controller.py  # Godot subprocess management
│   ├── scene_builder.py      # Structured .tscn manipulation (read/create/modify)
│   └── vision_qa.py          # Screen capture and visual QA
├── scripts/
│   └── setup_and_run.sh     # One-click Ubuntu setup
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

- **Python** 3.10 or later
- **Godot** 4.7 (recommended)
- **OS** Linux (Ubuntu 22.04+ recommended)

## License

MIT
