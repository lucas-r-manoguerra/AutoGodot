# Architecture

This document describes the system architecture of AutoGodot, how the components interact, and the design philosophy behind each decision.

## System Overview

AutoGodot is a Python-based MCP (Model Context Protocol) server that enables AI agents to interact with Godot 4.7 game projects. The framework acts as a bridge between the AI agent (which speaks MCP) and the Godot engine (which speaks CLI/GDScript).

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent (LLM)                           │
│            Claude Desktop / VS Code / OpenCode              │
│                                                             │
│  User: "Create a player character with movement"            │
│  Agent decides to call write_game_file()                    │
└──────────────────────┬──────────────────────────────────────┘
                       │  MCP Protocol (JSON-RPC over stdio)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AutoGodot MCP Server                  │
│                      (Python)                               │
│                                                             │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ mcp_server  │  │ godot_controller │  │  vision_qa    │  │
│  │   (.py)     │  │     (.py)        │  │    (.py)      │  │
│  │             │  │                  │  │               │  │
│  │ • 3 tools   │  │ • subprocess     │  │ • mss capture │  │
│  │ • Pydantic  │  │ • timeout/kill   │  │ • Pillow resize│  │
│  │ • stdio     │  │ • stdout/stderr  │  │ • Base64 out  │  │
│  └──────┬──────┘  └────────┬─────────┘  └───────┬───────┘  │
└─────────┼──────────────────┼─────────────────────┼──────────┘
          │                  │                     │
          │  subprocess.Popen│          mss (screen capture)
          ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Godot 4.x Engine                          │
│                                                             │
│  • Headless mode for testing (--headless)                   │
│  • GUI mode for visual QA                                   │
│  • CLI for project management                               │
│                                                             │
│  ┌─────────────────┐    ┌────────────────────────────────┐  │
│  │ GDScript files   │    │ Game running (for screenshots) │  │
│  │ (.gd, .tscn)     │    │                                │  │
│  └─────────────────┘    └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. MCP Server (`core/mcp_server.py`)

**Role:** Protocol handler. Receives JSON-RPC requests from the AI agent, dispatches to the correct tool, and returns structured responses.

**Key responsibilities:**
- Registers tools with typed input schemas (Pydantic models)
- Handles stdio transport (reads from stdin, writes to stdout)
- Validates all inputs before passing to subsystems
- Formats responses for LLM consumption

**Design decisions:**
- Uses `MCPServer` from the official `mcp` Python SDK (Anthropic)
- All tool inputs are Pydantic `BaseModel` subclasses for strict validation
- Logs go to stderr (MCP uses stdout for protocol messages)
- Async tool functions to support concurrent operations

### 2. Godot Controller (`core/godot_controller.py`)

**Role:** Subprocess manager. Spawns Godot processes, captures output, enforces timeouts.

**Key responsibilities:**
- Build Godot CLI commands from tool parameters
- Launch Godot as async subprocess (`asyncio.create_subprocess_exec`)
- Enforce hard timeouts with `asyncio.wait_for` + `proc.kill()`
- Capture and return stdout/stderr

**Design decisions:**
- **Hard kill guarantee:** Every Godot process has a maximum lifetime. If it exceeds the timeout, `proc.kill()` is called immediately — no graceful shutdown, no waiting. This prevents infinite loops caused by buggy AI-generated code.
- **Non-blocking:** All operations are async. The MCP server never blocks waiting for Godot.
- **Stateless:** Each `run_godot_test` call spawns a fresh Godot process. No persistent connection. This is simpler and more reliable than maintaining a long-lived Godot instance.
- **Output truncation:** Console output is capped at 8000 characters to avoid overwhelming the LLM context window.

### 3. Vision QA (`core/vision_qa.py`)

**Role:** Screen capture and image processing. Takes screenshots of the running game and returns them as Base64 JPEG for visual QA.

**Key responsibilities:**
- Capture the primary monitor using `mss` (fast, cross-platform)
- Resize images with Pillow (preserve aspect ratio)
- Encode to JPEG and Base64 for MCP response

**Design decisions:**
- **mss over python-xlib:** `mss` is faster, simpler, and doesn't require X11 configuration. It uses XComposite on Linux, which works without special permissions.
- **JPEG over PNG:** Smaller file sizes for LLM consumption. Quality is configurable (default 85).
- **Resize before encode:** Reduces the data the LLM needs to process. Default max 1280x720.

## Transport Protocol

### Why stdio?

The MCP server uses **stdio transport** (stdin/stdout) because:

1. **Universal compatibility:** Every MCP client supports stdio. HTTP requires additional configuration.
2. **Security:** No network ports are opened. The server runs as a child process of the MCP client.
3. **Simplicity:** No server startup, no port management, no CORS configuration.
4. **Claude Desktop default:** Claude Desktop expects stdio for local MCP servers.

### How stdio works

```
AI Client                          MCP Server (Python)
   │                                      │
   │  ──── JSON-RPC request (stdin) ────> │
   │                                      │  parse request
   │                                      │  validate inputs
   │                                      │  call tool function
   │                                      │  format response
   │  <─── JSON-RPC response (stdout) ─── │
   │                                      │
```

The server reads JSON-RPC messages from stdin, processes them, and writes responses to stdout. All logging goes to stderr so it doesn't interfere with the protocol.

## Design Philosophy

### 1. Zero Configuration for End Users

The `setup_and_run.sh` script automates everything:
- Detects Python and Godot installations
- Creates isolated virtual environments
- Injects MCP config into Claude Desktop
- The user runs one command and the system is ready

### 2. Hard Safety Rails

- **Path traversal protection:** All file writes are validated against the project root
- **Timeout enforcement:** No Godot process can run indefinitely
- **Process isolation:** Each operation is a fresh process, no shared state
- **Input validation:** Pydantic schemas reject invalid inputs before they reach Godot

### 3. LLM-Friendly Responses

- Console output is truncated to avoid context overflow
- Error messages include actionable information
- Responses are structured (not raw dumps) for easy parsing
- Visual QA returns Base64 that the LLM can directly process

### 4. Stateless by Default

No persistent Godot instance, no editor plugin, no GDExtension. Each operation is independent. This means:
- No state corruption between operations
- No plugin installation required per project
- No conflicts with existing Godot addons
- Simpler debugging and testing

## Comparison with Reference Projects

See [02-reference-analysis.md](./02-reference-analysis.md) for a detailed comparison with:
- **godot-mcp** (Coding-Solo): TypeScript MCP server, headless GDScript approach
- **Godot-MCP-Native** (yurineko73): Pure GDScript MCP server inside Godot editor

## File Structure

```
autogodot/
├── core/
│   ├── __init__.py          # Package marker
│   ├── mcp_server.py        # MCP protocol handler + tool definitions
│   ├── godot_controller.py  # Godot subprocess management
│   └── vision_qa.py         # Screen capture + image processing
├── scripts/
│   └── setup_and_run.sh     # One-click Ubuntu setup
├── config/
│   └── claude_desktop_config.example.json
├── docs/                    # This documentation
└── requirements.txt         # Python dependencies
```

## Future Evolution

Current architecture is intentionally simple (3 tools, stateless). Future versions may add:

1. **Scene manipulation tools** — Create nodes, add sprites, modify scene trees
2. **Persistent Godot connection** — WebSocket or TCP for real-time editor integration
3. **Runtime introspection** — Inspect running game state (like Godot-MCP-Native's Runtime Probe)
4. **Undo/Redo support** — Integration with Godot's EditorUndoRedoManager
5. **Multi-project support** — Manage multiple Godot projects simultaneously

These additions will follow the same design principles: safety first, LLM-friendly, zero configuration.
