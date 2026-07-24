# MCP Tools Reference

This document provides the complete API reference for every tool exposed by the AutoGodot MCP server.

## Tool Overview

| Tool | Purpose | Modifies Files | Spawns Process | Captures Screen |
|------|---------|:--------------:|:--------------:|:---------------:|
| `write_game_file` | Create/edit Godot source files | ✅ | — | — |
| `run_godot_test` | Run Godot and capture logs | — | ✅ | — |
| `capture_game_screen` | Screenshot for visual QA | — | — | ✅ |

---

## 1. `write_game_file`

### Purpose

Create or overwrite a text-based Godot project file. Use this to write GDScript source code (`.gd`), scene definitions (`.tscn`), resources (`.tres`), configuration files (`.cfg`), or any other text asset.

### Input Schema

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `file_path` | `string` | ✅ | — | Relative path inside the Godot project directory. Examples: `"scripts/player.gd"`, `"scenes/main.tscn"`, `"addons/my_plugin/plugin.cfg"` |
| `content` | `string` | ✅ | — | Full text content to write. Overwrites existing file completely. |
| `create_dirs` | `boolean` | — | `true` | If `true`, creates intermediate directories when they don't exist. |

### Output

**Success:**
```
OK: Wrote 1234 bytes to scripts/player.gd
```

**Error (path traversal):**
```
ERROR: Path traversal detected. '../../etc/passwd' escapes the project root.
```

**Error (OS error):**
```
ERROR writing scripts/player.gd: [Errno 13] Permission denied: '/path/to/project/scripts/player.gd'
```

### Behavior

1. Resolves `file_path` against the configured Godot project root directory
2. Validates that the resolved path is inside the project root (prevents path traversal)
3. Creates parent directories if `create_dirs` is `true`
4. Writes content as UTF-8, completely replacing any existing file
5. Returns confirmation with byte count

### Security

- **Path traversal protection:** Any `..` in the path that would escape the project root is rejected
- **No binary files:** Content is written as UTF-8 text. Binary file writing is not supported.
- **Overwrites silently:** There is no merge or append mode. Content fully replaces the existing file.

### Examples

**Create a new GDScript:**
```json
{
  "file_path": "scripts/player.gd",
  "content": "extends CharacterBody2D\n\nfunc _physics_process(delta: float) -> void:\n    velocity = Vector2.ZERO\n    if Input.is_action_pressed(\"move_right\"):\n        velocity.x += 1\n    move_and_slide()\n"
}
```

**Create a scene file:**
```json
{
  "file_path": "scenes/enemies/goblin.tscn",
  "content": "[gd_scene load_steps=2 format=3]\n\n[ext_resource type=\"Script\" path=\"res://scripts/goblin.gd\" id=\"1\"]\n\n[node name=\"Goblin\" type=\"CharacterBody2D\"]\nscript = ExtResource(\"1\")\n",
  "create_dirs": true
}
```

---

## 2. `run_godot_test`

### Purpose

Launch the Godot engine to run a specific scene or the project's main scene. Captures all console output (stdout and stderr) and enforces a hard timeout. Useful for testing game logic, validating scene loads, or checking for runtime errors.

### Input Schema

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `scene_path` | `string \| null` | — | `null` | Relative path to a `.tscn` scene. If `null`, the project's main scene (from `project.godot`) is launched. |
| `timeout_seconds` | `number` | — | `30.0` | Maximum seconds before the process is force-killed. Range: 1.0–300.0. |
| `extra_args` | `string[]` | — | `[]` | Additional CLI arguments passed to Godot. Examples: `["--verbose"]`, `["--render-thread=0"]` |

### Output

Returns a multi-section text response:

```
--- Godot Test Run [SUCCESS] ---
Scene: scenes/main.tscn
Exit code: 0
Duration: 5.23s
Timed out: no

--- Console Output ---
Godot Engine v4.3.stable.official
...
```

Or on failure:

```
--- Godot Test Run [FAILED] ---
Scene: scenes/main.tscn
Exit code: 1
Duration: 30.01s
Timed out: yes

--- Console Output ---
[TIMEOUT] Godot process was force-killed after 30.0 seconds
```

### Behavior

1. Builds the Godot CLI command: `godot --path <project_dir> [--scene <scene_path>] [extra_args...]`
2. Launches Godot as an async subprocess
3. Waits for completion with the specified timeout
4. If timeout expires: force-kills the process (`proc.kill()`) and marks `timed_out: true`
5. Captures stdout and stderr, truncates to 8000 characters if needed
6. Returns structured output with exit code, duration, and console text

### Godot CLI Flags

The tool uses these Godot flags:
- `--path <dir>` — Sets the project directory
- `--scene <path>` — Runs a specific scene (instead of main scene)

Additional flags can be passed via `extra_args`:
- `--verbose` — Verbose output
- `--headless` — Run without window (for logic-only testing)
- `--render-thread=0` — Disable rendering threads

### Timeout Behavior

**Critical safety feature:** The timeout is a HARD limit. When exceeded:
1. `proc.kill()` is called immediately (SIGKILL on Linux)
2. No graceful shutdown is attempted
3. The response includes `[TIMEOUT]` marker in stderr
4. `timed_out: true` is set in the result

This prevents infinite loops caused by buggy AI-generated code.

### Examples

**Run the main scene:**
```json
{}
```

**Run a specific test scene with verbose output:**
```json
{
  "scene_path": "scenes/tests/test_player.gd",
  "timeout_seconds": 60.0,
  "extra_args": ["--verbose"]
}
```

---

## 3. `capture_game_screen`

### Purpose

Capture a screenshot of the running game window for visual QA. Takes a screenshot of the primary monitor, resizes it to fit within specified dimensions, and returns it as a Base64-encoded JPEG string that the AI agent can process.

### Input Schema

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `max_width` | `integer` | — | `1280` | Maximum output width in pixels. Range: 320–3840. |
| `max_height` | `integer` | — | `720` | Maximum output height in pixels. Range: 240–2160. |
| `quality` | `integer` | — | `85` | JPEG compression quality. Range: 10–100. |

### Output

Returns a JSON string (not a structured JSON response — the LLM parses the string):

```json
{
  "status": "success",
  "width": 1280,
  "height": 720,
  "format": "jpeg",
  "quality": 85,
  "base64_data": "/9j/4AAQSkZJRg..."
}
```

### Behavior

1. Uses `mss` to capture the primary monitor (full screen)
2. Converts the raw capture to a PIL Image
3. Resizes to fit within `max_width × max_height` (preserves aspect ratio)
4. Encodes to JPEG with the specified quality
5. Base64-encodes the JPEG bytes
6. Returns structured response with dimensions and Base64 data

### Capture Notes

- **Primary monitor only:** `mss` captures the full primary monitor, not a specific window. For game-specific capture, the game window should be focused and maximized on the target monitor.
- **No X11 configuration required:** `mss` uses XComposite on Linux, which works without special permissions.
- **Resize is proportional:** The image is scaled to fit within the bounds while preserving aspect ratio. If the original is smaller than the bounds, no upscaling occurs.

### Visual QA Workflow

A typical visual QA flow:

1. AI agent calls `run_godot_test` to launch the game
2. AI agent calls `capture_game_screen` to get a screenshot
3. AI agent processes the Base64 image to evaluate:
   - Scene layout and composition
   - UI element positioning
   - Sprite placement and scaling
   - Color palette and visual consistency
   - Error states (missing textures, broken layouts)

### Examples

**Default capture (1280×720, quality 85):**
```json
{}
```

**High-quality capture for detailed inspection:**
```json
{
  "max_width": 1920,
  "max_height": 1080,
  "quality": 95
}
```

**Low-bandwidth capture (smaller, lower quality):**
```json
{
  "max_width": 640,
  "max_height": 480,
  "quality": 50
}
```

---

## Error Handling

All tools follow consistent error handling:

1. **Validation errors** are caught by Pydantic before the tool function runs. The MCP SDK returns a structured error response automatically.

2. **Runtime errors** are caught by the tool function and returned as text responses starting with `ERROR:`. The AI agent can parse these and retry with corrected parameters.

3. **Process errors** (Godot not found, timeout exceeded) include diagnostic information to help the AI agent understand what went wrong.

## Tool Interaction Patterns

### Pattern: Write → Run → Capture

The most common workflow for visual QA:

```
1. write_game_file("scripts/player.gd", "...")  → OK: Wrote 456 bytes
2. run_godot_test("scenes/game.tscn", 30)        → SUCCESS, exit 0
3. capture_game_screen(1280, 720)                 → {base64: "..."}
```

### Pattern: Iterative Development

```
1. write_game_file("scripts/player.gd", "v1")  → OK
2. run_godot_test()                              → FAILED: syntax error in line 5
3. write_game_file("scripts/player.gd", "v2")  → OK (fixed)
4. run_godot_test()                              → SUCCESS
5. capture_game_screen()                         → {base64: "..."}
6. AI evaluates screenshot, decides to adjust
7. write_game_file("scripts/player.gd", "v3")  → OK
```
