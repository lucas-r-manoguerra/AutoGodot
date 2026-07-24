# Design: Scene Builder (.tscn) — 3-Tool MVP

## Technical Approach

Add `SceneBuilder` in `core/scene_builder.py` wrapping `godot-parser` (stevearc, v0.1.7). Three `@mcp.tool()` functions in `mcp_server.py` delegate to it. Same module-level singleton pattern as `GodotController`/`VisionQA`.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| godot-parser API | High-level (`GDScene`, `use_tree`, `Node`) | Low-level `GDFile`/`GDSection` | Auto-manages resource IDs and tree structure |
| Scene tree JSON | Flat node list with `parent` paths | Recursive tree | Maps directly to TSCN `parent=` attribute |
| Property values | String (`"Vector2(100, 200)"`) | Typed objects | Matches TSCN serialization; no type inference |
| Error handling | `try/except` → `"ERROR: ..."` string | Exceptions propagate | Matches existing tool return pattern |
| Module structure | Separate file + imports | Inline in mcp_server.py | Follows `GodotController`/`VisionQA` separation |

## Scene JSON Schema

```json
{
  "resources": [{"type": "PackedScene", "path": "res://Player.tscn", "id": 1}],
  "sub_resources": [],
  "nodes": [
    {
      "name": "Main", "type": "Node2D", "parent": ".",
      "properties": {"position": "Vector2(0, 0)"},
      "groups": [],
      "connections": [{"signal": "ready", "target": "Player", "method": "_on_ready", "flags": 0}]
    },
    {
      "name": "Player", "type": "KinematicBody2D", "parent": ".",
      "properties": {"script": "ExtResource(1)"},
      "groups": ["player"], "connections": []
    }
  ]
}
```

## SceneBuilder Class

```python
class SceneBuilder:
    def __init__(self, project_dir: Path) -> None: ...
    def read_scene(self, scene_path: str) -> dict: ...
    def create_scene(self, scene_path: str, definition: dict) -> str: ...
    def modify_scene(self, scene_path: str, operations: list[dict]) -> str: ...
```

**godot-parser integration:**
- **Read**: `load(path)` → `scene.root_tree` → recursive `_flatten_tree(root)` → flat list
- **Create**: `GDScene()` → `add_ext_resource()` for each resource → `use_tree()` context builds `Node` tree → `scene.write(path)`
- **Modify**: `load(path)` → `use_tree()` → `tree.get_node()` + property assignment or `add_child(Node(...))` → `scene.write(path)`

## Input Models

```python
class NodeDefinition(BaseModel):
    name: str
    type: str
    parent: str = "."
    properties: dict[str, str] = {}
    groups: list[str] = []
    connections: list[dict] = []

class ResourceRef(BaseModel):
    type: str
    path: str
    id: int

class SceneDefinition(BaseModel):
    resources: list[ResourceRef] = []
    sub_resources: list[dict] = []
    nodes: list[NodeDefinition]

class ModifyOperation(BaseModel):
    action: Literal["add_node", "remove_node", "set_property", "connect_signal"]
    target: str | None = None      # Node path for set_property/remove_node/connect_signal
    parent: str | None = None      # For add_node
    name: str | None = None        # For add_node
    type: str | None = None        # For add_node
    property: str | None = None    # For set_property
    value: str | None = None       # For set_property
    signal: str | None = None      # For connect_signal
    method: str | None = None      # For connect_signal

class ReadSceneInput(BaseModel):
    scene_path: str

class CreateSceneInput(BaseModel):
    scene_path: str
    definition: SceneDefinition

class ModifySceneInput(BaseModel):
    scene_path: str
    operations: list[ModifyOperation]
```

## Error Handling

Path traversal check identical to `write_game_file`: `(GODOT_PROJECT / scene_path).resolve()` + `startswith` guard. All tool functions wrap `SceneBuilder` calls in `try/except Exception` returning `"ERROR: ..."` strings.

## Modify Operations

```json
{"action": "add_node", "parent": "Player", "name": "Sprite2D", "type": "Sprite2D"}
{"action": "remove_node", "target": "Player/Camera2D"}
{"action": "set_property", "target": "Player", "property": "position", "value": "Vector2(100, 200)"}
{"action": "connect_signal", "target": "Player", "signal": "hit", "method": "_on_player_hit"}
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `core/scene_builder.py` | Create | `SceneBuilder` class, ~150 lines |
| `core/mcp_server.py` | Modify | +3 input models, +3 tool functions |
| `tests/test_scene_builder.py` | Create | Unit + integration tests |
| `tests/conftest.py` | Modify | Add `sample_tscn` and `scene_builder` fixtures |
| `pyproject.toml` | Modify | Add `godot-parser>=0.1.7` to dependencies |

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | `read_scene` | Mock `godot_parser.load`, verify dict output |
| Unit | `create_scene` | Mock `GDScene`/`Node`, verify `write()` called correctly |
| Unit | `modify_scene` | Mock `load`+`use_tree`, verify operations applied |
| Unit | Path traversal | All 3 tools with `../../etc/passwd` |
| Integration | Round-trip | Create scene → read back → compare nodes |
| MCP | Registration | Verify all 3 tools callable |

Mock `godot_parser` at `core.scene_builder` import level; do NOT mock filesystem. `conftest.py` gets a `SAMPLE_TSCN` constant (format=3 with ext_resource, sub_resource, nested nodes) and `sample_tscn`/`scene_builder` fixtures.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration. `godot-parser` is pure Python, zero runtime deps. Add to `pyproject.toml` and install. Existing tools unaffected.

## Open Questions

- [ ] Does `load()` + `write()` preserve UIDs on format=3 files, or strip them? Test with real .tscn during impl.
- [ ] Exact API for adding signal connections via `use_tree()` — verify during impl.
