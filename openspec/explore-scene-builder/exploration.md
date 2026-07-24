# Exploration: Scene Builder (.tscn) for AutoGodot

## Current Architecture Summary

AutoGodot follows a clean 3-module architecture:

| Module | Role | Pattern |
|--------|------|---------|
| `core/mcp_server.py` | Protocol handler + tool definitions | FastMCP `@mcp.tool()` decorators, Pydantic input models, string responses |
| `core/godot_controller.py` | Godot subprocess management | Async subprocess, hard timeout, stdout/stderr capture |
| `core/vision_qa.py` | Screen capture + image processing | mss + Pillow, Base64 JPEG output |

**Key conventions:**
- Tool functions are `async`, return `str` (not JSON)
- Input validation via Pydantic `BaseModel` with `Field()` descriptions
- Path traversal protection on all file writes (resolve + prefix check)
- Responses formatted for LLM consumption (structured text, not raw dumps)
- Subsystems instantiated as module-level singletons
- Tests use `pytest-asyncio` (auto mode), `monkeypatch` for isolation
- Coverage threshold is 40% (lenient)

**What already exists for scene creation:**
The `write_game_file` tool can already write `.tscn` content as raw text. The gap is that the AI must generate the entire TSCN text manually — no parsing, no structured manipulation, no validation.

---

## Godot .tscn Format Analysis

### Structure (5 sections, in order)

```
[gd_scene format=3 uid="uid://xxxxx"]       ← 1. File descriptor

[ext_resource type="Script" path="res://..." id="1_abc"]  ← 2. External resources
[ext_resource type="Texture2D" uid="uid://..." path="res://..." id="2_def"]

[sub_resource type="SphereShape3D" id="SphereShape3D_xyz"]  ← 3. Internal resources
radius = 1.0

[node name="Player" type="CharacterBody2D"]  ← 4. Nodes (scene tree)
script = ExtResource("1_abc")

[node name="Sprite" type="Sprite2D" parent="."]
texture = ExtResource("2_def")

[connection signal="area_entered" from="." to="." method="_on_area_entered"]  ← 5. Connections
```

### Key Syntax Rules

| Element | Syntax | Example |
|---------|--------|---------|
| Header | `[section_type key=value ...]` | `[gd_scene format=3 uid="uid://abc"]` |
| External ref | `ExtResource("id")` | `ExtResource("1_abc")` |
| Internal ref | `SubResource("id")` | `SubResource("SphereShape3D_xyz")` |
| Node path | `"Parent/Child"` or `"."` for root children | `parent="Player/Head"` |
| Properties | `key = value` (indent matters for dicts) | `position = Vector2(100, 200)` |
| Types | Constructor syntax | `Color(1, 0, 0, 1)`, `Vector3(0, 1, 0)` |
| UIDs | `uid://` string prefix (Godot 4.6+) | `uid://cecaux1sm7mo0` |
| Comments | `;` prefix (discarded on save) | `; This is a comment` |

### Critical Gotchas

1. **Default values are omitted** — A node with `position = Vector2(0, 0)` won't have that property in the file. Adding it back won't break anything, but Godot strips it on re-save.

2. **UIDs are mandatory in Godot 4.6+** — Scenes require `uid="uid://..."` in the header. External resources need UIDs too. We need to generate valid UIDs or skip them (Godot will assign on first open).

3. **`load_steps` is deprecated** — Pre-4.6 scenes had `load_steps=N` in the header. Godot 4.6+ ignores it but old files may still have it.

4. **`unique_id` on nodes** — Godot 4.6+ adds `unique_id=<int>` to nodes. Not strictly required but present in editor-saved scenes.

5. **Order matters for internal resources** — A SubResource must be declared before any other SubResource references it.

6. **Parent paths are absolute from root** — Child nodes use `parent="RootNode/ChildNode"`, NOT relative paths. Direct children of root use `parent="."`.

7. **Scene inheritance** — A scene can inherit from another via `[gd_scene ... instance=ExtResource("id")]`. The root node of the inherited scene becomes non-editable.

8. **Properties with special types** — `NodePath(...)`, `ExtResource(...)`, `SubResource(...)` are special constructor forms, not plain strings.

### .tres Format

Identical syntax to .tscn but for standalone resources:
```
[gd_resource type="StandardMaterial3D" format=3 uid="uid://abc"]

[ext_resource type="Texture2D" path="res://tex.png" id="1"]

[resource]
albedo_texture = ExtResource("1")
albedo_color = Color(1, 0, 0, 1)
```

---

## Affected Areas

- `core/mcp_server.py` — New tool registrations + input models
- `core/scene_builder.py` — **NEW** module: TSCN parser/builder (the core logic)
- `tests/test_scene_builder.py` — **NEW** unit tests for parser/builder
- `tests/test_mcp_server.py` — Additional tool registration tests
- `pyproject.toml` — New dependency (`godot-parser` or custom)
- `requirements.txt` — Updated deps

---

## Approach Comparison

### Approach A: Use `godot-parser` library (stevearc)

| Aspect | Detail |
|--------|--------|
| **Pros** | Battle-tested parser, handles edge cases, MIT license, high-level API (GDScene, Node), low-level fallback |
| **Cons** | Last updated March 2025, format=3 support unverified, 80 stars (not huge), `pyparsing` dependency, inheritance gaps |
| **Effort** | Low — wrap existing API in MCP tools |
| **Risk** | Library may not handle Godot 4.6+ UIDs or latest format quirks |

### Approach B: Build custom parser (text-based, minimal)

| Aspect | Detail |
|--------|--------|
| **Pros** | Full control, no dependency risk, tailored to our exact needs, can handle format=3 UIDs from day one |
| **Cons** | More work, must handle all Godot value types (Vector2/3/4, Color, Transform2D/3D, etc.), edge cases |
| **Effort** | Medium-High — regex/state-machine parser + builder |
| **Risk** | Godot value type parsing is a rabbit hole (arrays, dicts, nested constructors) |

### Approach C: Hybrid — use `godot-parser` for parsing, custom builder for creation

| Aspect | Detail |
|--------|--------|
| **Pros** | Leverage parser for read operations (hardest part), custom builder for write (simpler, we control output) |
| **Cons** | Two codepaths to maintain, potential format inconsistencies |
| **Effort** | Medium |
| **Risk** | Mixed approach may confuse contributors |

### Recommendation: **Approach A (godot-parser) with fallback**

Use `godot-parser` as the primary library. It handles parsing AND writing. If it fails on specific format=3 features, we can patch or work around. The alternative of building our own parser for Godot's entire value type system is a significant undertaking that doesn't serve our core mission (helping AI build games).

If `godot-parser` proves insufficient, we can migrate to a custom parser incrementally — but starting with the library saves weeks.

---

## Proposed Tool Surface (MVP)

### Tool 1: `read_scene`

**Purpose:** Parse a .tscn file and return its structured content (nodes, resources, connections).

**Input:**
```python
class ReadSceneInput(BaseModel):
    file_path: str  # Relative path to .tscn file
```

**Output:** JSON-like structured text describing:
- Scene header (format, uid)
- External resources (id, type, path)
- Internal resources (id, type, properties)
- Node tree (name, type, parent, properties)
- Connections (signal, from, to, method)

**Why this matters:** The AI can understand existing scenes before modifying them. Currently it would need to parse raw TSCN text manually.

---

### Tool 2: `create_scene`

**Purpose:** Create a new .tscn file from a structured node tree definition.

**Input:**
```python
class CreateSceneInput(BaseModel):
    file_path: str              # Where to save the .tscn
    root_name: str              # Name of root node
    root_type: str              # Type of root node (e.g., "Node2D", "CharacterBody2D")
    nodes: list[SceneNodeDef]   # Child nodes to add
    connections: list[SignalDef] # Optional signal connections

class SceneNodeDef(BaseModel):
    name: str
    type: str
    parent: str = "."           # Parent path (default: root)
    properties: dict[str, str] = {}  # Key-value pairs as strings

class SignalDef(BaseModel):
    signal_name: str
    from_node: str
    to_node: str
    method: str
```

**Why this matters:** The AI can declaratively describe a scene tree and get a valid .tscn. No need to understand TSCN syntax.

---

### Tool 3: `modify_scene`

**Purpose:** Make targeted changes to an existing .tscn file.

**Input:**
```python
class ModifySceneInput(BaseModel):
    file_path: str
    operations: list[SceneOperation]  # One or more operations

class SceneOperation(BaseModel):
    action: str  # "add_node", "remove_node", "set_property", "add_connection", "remove_connection"
    target: str  # Node path or identifier
    params: dict[str, str] = {}  # Operation-specific params
```

**Why this matters:** Surgical edits without rewriting the whole file. Add a node, change a property, remove a connection.

---

### Tool 4: `list_scene_nodes`

**Purpose:** Quick query to get just the node tree (names, types, hierarchy) without full property details.

**Input:**
```python
class ListSceneNodesInput(BaseModel):
    file_path: str
```

**Output:** Tree-formatted text:
```
Root (Node2D)
├── Player (CharacterBody2D)
│   ├── Sprite2D
│   └── CollisionShape2D
├── Camera2D
└── UI (CanvasLayer)
    ├── HealthBar
    └── ScoreLabel
```

**Why this matters:** Lightweight scene introspection. The AI often needs to know "what's in this scene" without all the property details.

---

### Tool 5: `validate_scene`

**Purpose:** Check if a .tscn file is syntactically valid and report issues.

**Input:**
```python
class ValidateSceneInput(BaseModel):
    file_path: str
```

**Output:** Validation report:
- Syntax validity
- Missing resource references
- Duplicate node names
- Orphaned connections

**Why this matters:** Catch errors before running Godot. The AI can self-correct.

---

## Scope Boundaries

### IN for v1
- ✅ Read/parse .tscn files (format=3, Godot 4.x)
- ✅ Create new .tscn files from structured definitions
- ✅ Modify existing .tscn files (add/remove nodes, set properties)
- ✅ List node tree (names, types, hierarchy)
- ✅ Validate .tscn syntax
- ✅ Handle ext_resource and sub_resource references
- ✅ Basic .tres support (same format)
- ✅ Signal connections

### OUT for v1
- ❌ Scene inheritance (complex, edge-case heavy)
- ❌ Animation data manipulation (deeply nested, rarely AI-generated)
- ❌ ArrayMesh / 3D mesh data (binary-like, not AI-relevant)
- ❌ Binary .scn/.res files (not text-based)
- ❌ TileMap / TileSet editing (complex resource graph)
- ❌ Real-time sync with Godot editor
- ❌ Undo/redo integration
- ❌ UID generation (let Godot assign on first open, or use a simple counter)

### DEFERRED
- ⏳ Scene inheritance support
- ⏳ Advanced resource editing (materials, shaders)
- ⏳ Batch operations across multiple scenes
- ⏳ Scene comparison / diff

---

## Risks and Unknowns

### High Risk

1. **`godot-parser` format=3 compatibility** — The library was last updated March 2025 and may not handle Godot 4.6+ UID syntax. Need to verify with real .tscn files from a Godot 4.6+ project.

2. **Godot value type parsing** — Types like `Transform3D(...)`, `PackedFloat32Array(...)`, nested arrays/dicts are complex. `godot-parser` handles most, but edge cases exist.

### Medium Risk

3. **UID generation** — Godot 4.6+ requires UIDs. We can either:
   - Skip UIDs (Godot assigns on first open — works but triggers reimport)
   - Generate random UIDs (format: `uid://` + base62-like string)
   - Use a simple counter (less unique but deterministic)

4. **Property defaults** — We need to know Godot's default values to avoid writing unnecessary properties. The `godot-parser` library doesn't track defaults — we'd need a lookup table for common types.

5. **Node unique_id** — Godot 4.6+ adds integer `unique_id` to nodes. Not required for loading but present in editor-saved files.

### Low Risk

6. **Performance** — TSCN files are small text. Parsing speed is irrelevant for MCP tool usage.

7. **Thread safety** — MCP tools run sequentially per client. No concurrency concerns.

8. **Backward compatibility** — Existing `write_game_file` tool still works for raw TSCN writing. Scene builder is additive.

---

## Recommended Approach: Phased Implementation

### Phase 1: Foundation (1-2 days)

1. **Add `godot-parser` dependency** to `pyproject.toml`
2. **Create `core/scene_builder.py`** module with:
   - `read_scene(path) -> SceneData` — Parse .tscn, return structured dict
   - `create_scene(path, definition) -> None` — Write new .tscn from definition
   - `modify_scene(path, operations) -> None` — Apply changes to existing .tscn
3. **Register tools** in `mcp_server.py`:
   - `read_scene` → calls `scene_builder.read_scene()`
   - `create_scene` → calls `scene_builder.create_scene()`
   - `modify_scene` → calls `scene_builder.modify_scene()`

### Phase 2: Polish (1 day)

4. **Add `list_scene_nodes`** — Lightweight tree view (reuse read_scene, format output)
5. **Add `validate_scene`** — Parse + check for common issues
6. **Write comprehensive tests** — Cover all tools with unit tests + integration tests

### Phase 3: Edge Cases (ongoing)

7. **Scene inheritance** — Handle `instance=` in scene header
8. **Advanced properties** — Handle NodePath, ExtResource, SubResource constructors properly
9. **UID handling** — Decide on strategy (skip vs generate)

---

## Implementation Sketch

### `core/scene_builder.py` (high-level)

```python
"""Scene Builder — Parse and create Godot .tscn scene files."""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SceneBuilder:
    """Build and manipulate Godot .tscn scene files."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()

    def read_scene(self, file_path: str) -> dict[str, Any]:
        """Parse a .tscn file and return structured data."""
        # Uses godot-parser to parse
        # Returns dict with header, ext_resources, sub_resources, nodes, connections
        ...

    def create_scene(
        self,
        file_path: str,
        root_name: str,
        root_type: str,
        nodes: list[dict[str, Any]],
        connections: list[dict[str, Any]] | None = None,
    ) -> str:
        """Create a new .tscn file from a structured definition."""
        # Uses godot-parser GDScene API
        # Returns confirmation message
        ...

    def modify_scene(
        self,
        file_path: str,
        operations: list[dict[str, Any]],
    ) -> str:
        """Apply modifications to an existing .tscn file."""
        # Uses godot-parser to load, modify, write
        # Returns confirmation message
        ...
```

### Test fixtures needed

```python
# tests/conftest.py additions
@pytest.fixture
def sample_tscn(tmp_godot_project: Path) -> Path:
    """Create a minimal .tscn file for testing."""
    scene = tmp_godot_project / "scenes" / "test.tscn"
    scene.parent.mkdir(parents=True)
    scene.write_text("""[gd_scene format=3]

[node name="Root" type="Node2D"]

[node name="Child" type="Sprite2D" parent="."]
""")
    return scene
```

---

## Ready for Proposal

**Yes** — the exploration is complete. The orchestrator should:

1. Confirm the `godot-parser` dependency approach (or request custom parser)
2. Confirm the 5-tool surface (read_scene, create_scene, modify_scene, list_scene_nodes, validate_scene) or trim to MVP subset
3. Proceed to proposal phase with this analysis

The minimum viable scene builder is **read_scene + create_scene** — two tools that let an AI agent understand and create scenes. modify_scene, list_scene_nodes, and validate_scene are valuable additions but can be deferred.
