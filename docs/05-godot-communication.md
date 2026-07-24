# Godot Communication

This document explains how AutoGodot communicates with the Godot engine, the tradeoffs of our approach, and how it compares to alternative methods.

## Communication Model

```
MCP Server (Python)
       │
       │  subprocess.Popen (asyncio.create_subprocess_exec)
       │
       ▼
Godot Process (one per operation)
       │
       ├── stdout → captured and returned to AI agent
       ├── stderr → captured and returned to AI agent
       └── exit code → indicates success (0) or failure (non-zero)
```

### Key Characteristic: Stateless Subprocess

Each operation spawns a **fresh Godot process**. There is no persistent connection, no editor plugin, and no shared state between operations.

**Example flow:**
```
AI Agent calls write_game_file() → Python writes file directly (no Godot needed)
AI Agent calls run_godot_test()  → Spawns Godot process → captures output → process exits
AI Agent calls capture_game_screen() → mss captures screen → no Godot process involved
```

## How Each Tool Communicates with Godot

### `write_game_file` — No Godot Process

This tool does **not** communicate with Godot at all. It writes files directly from Python using `pathlib.Path.write_text()`.

```
Python → filesystem → .gd/.tscn files
```

**Why:** Text files don't need Godot's API to create. GDScript is plain text. Scene files (`.tscn`) are also plain text (Godot's text-based scene format). Only binary resources (`.res`, `.scn`) require Godot's API.

**Implication:** You can write GDScript and scene files without Godot installed. But to validate them, you need Godot for `run_godot_test`.

### `run_godot_test` — Godot CLI Subprocess

This tool spawns Godot as a subprocess:

```bash
godot4 --path /project/dir [--scene scenes/test.tscn] [--verbose]
```

**Godot CLI flags used:**

| Flag | Purpose |
|------|---------|
| `--path <dir>` | Sets the project root directory |
| `--scene <path>` | Runs a specific scene instead of the main scene |
| `--verbose` | Enables verbose logging (optional, via `extra_args`) |
| `--headless` | Runs without window (optional, via `extra_args`) |

**What Godot does when spawned:**
1. Loads `project.godot` from the project directory
2. Initializes the engine (renderer, physics, audio, etc.)
3. Loads and runs the specified scene (or main scene)
4. Executes GDScript `_ready()`, `_process()`, `_physics_process()`, etc.
5. Writes output to stdout/stderr
6. Exits when the scene ends or is closed

**What we capture:**
- **stdout:** Engine messages, `print()` output from GDScript, resource loading logs
- **stderr:** Errors, warnings, stack traces, crash information
- **exit code:** `0` = success, non-zero = failure

### `capture_game_screen` — Screen Capture (mss)

This tool does **not** communicate with Godot. It uses `mss` to capture the primary monitor:

```
mss → XComposite (Linux) → raw pixels → Pillow resize → JPEG → Base64
```

**Why no Godot API:** Godot doesn't expose a "take screenshot" API via CLI. The simplest cross-platform approach is to capture the display directly. This works regardless of which application is rendering.

**Limitation:** `mss` captures the full monitor, not a specific window. The game window should be focused and visible for accurate capture.

## Why Stateless Subprocess?

### Alternative Approaches (Not Used)

| Approach | How It Works | Tradeoff |
|----------|-------------|----------|
| **Persistent Godot process** | Keep Godot running, send commands via pipe/socket | Complex, state corruption risk, harder timeout enforcement |
| **Editor plugin** | GDScript addon inside Godot editor | Requires plugin installation per project, conflicts with existing addons |
| **GDExtension** | C++/Rust shared library loaded by Godot | Requires compilation, platform-specific binaries |
| **Headless GDScript** | `godot --headless --script operations.gd` | Spawns a process per operation (same as us, but with GDScript overhead) |

### Why We Chose Stateless

1. **Reliability:** No state to corrupt between operations. Each operation starts fresh.
2. **Simplicity:** No connection management, no reconnection logic, no heartbeat.
3. **Safety:** Hard timeout is easy — just `proc.kill()` after N seconds.
4. **No Godot editor required:** The MCP server works without opening the Godot editor.
5. **No plugin conflicts:** Doesn't install anything into the Godot project.

### Tradeoffs

| Benefit | Cost |
|---------|------|
| No state corruption | Each operation has startup overhead (~1-2s for Godot) |
| No plugin installation | Can't access running editor's scene tree |
| Simple timeout enforcement | Can't inspect live game state |
| Works without editor | No undo/redo integration |

## Comparison with Reference Projects

### godot-mcp (TypeScript)

**Same approach:** Also uses stateless subprocess spawning.

**Differences:**
- They use Node.js `child_process.spawn()` → we use Python `asyncio.create_subprocess_exec`
- They have a GDScript dispatcher (`godot_operations.gd`) for complex operations → we write files directly from Python
- They run Godot headless for scene manipulation → we haven't implemented scene tools yet

### Godot-MCP-Native (GDScript)

**Different approach:** The MCP server runs **inside** the Godot editor process.

**Advantages of their approach:**
- Direct access to `EditorInterface`, `EditorUndoRedoManager`, etc.
- Real-time scene tree inspection
- Runtime Probe for live game introspection
- No subprocess overhead

**Advantages of our approach:**
- No Godot editor required to run the MCP server
- No plugin installation per project
- Hard timeout enforcement via process kill
- Simpler architecture

## Future: Persistent Godot Connection

If we need real-time editor integration in the future, we could add:

1. **WebSocket transport:** Keep a Godot process running, communicate via WebSocket
2. **Editor plugin mode:** Install a GDScript addon that opens a WebSocket server
3. **Runtime Probe:** Autoloaded node for live game introspection (like Godot-MCP-Native)

These would be **additive** — the current stateless subprocess approach remains the default.

## Timeout Deep Dive

### How Timeouts Work

```python
# In godot_controller.py
proc = await asyncio.create_subprocess_exec(*cmd, ...)
try:
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
except asyncio.TimeoutError:
    proc.kill()          # SIGKILL — immediate termination
    await proc.wait()    # Collect exit status
```

### Why SIGKILL, Not SIGTERM?

- **SIGTERM** asks the process to shut down gracefully. Godot might ignore it or take time to clean up.
- **SIGKILL** terminates immediately. The OS reclaims resources. No chance for the process to hang.

For an AI agent that might generate infinite loops or blocking code, SIGKILL is the only safe option.

### What Happens After Kill

1. The MCP server captures whatever stdout/stderr was written before the kill
2. The response includes `[TIMEOUT]` marker
3. The process is fully reaped (no zombie processes)
4. The MCP server is ready for the next operation
