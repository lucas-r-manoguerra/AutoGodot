# Scene Builder Specification

## Purpose

Enable AI agents to parse, create, and modify Godot 4.x `.tscn` scene files through structured JSON instead of raw text manipulation. Wraps `godot-parser` (stevearc, MIT) behind three MCP tools.

---

## Scene JSON Schema

All three tools share this representation. This is the canonical contract.

```json
{
  "header": {
    "godot_version": "4.2",
    "scene_format": 3
  },
  "resources": [
    {
      "type": "ext_resource",
      "id": "1",
      "path": "res://scripts/player.gd",
      "resource_type": "Script",
      "uid": "uid://abc123"
    },
    {
      "type": "sub_resource",
      "id": "sub_1",
      "resource_type": "CircleShape2D",
      "properties": { "radius": "32.0" }
    }
  ],
  "nodes": [
    {
      "name": "Main",
      "type": "Node2D",
      "parent": null,
      "properties": {},
      "groups": [],
      "connections": []
    },
    {
      "name": "Player",
      "type": "CharacterBody2D",
      "parent": ".",
      "properties": {
        "position": "Vector2(100, 200)",
        "script": "ext_resource(\"1\")"
      },
      "groups": ["player"],
      "connections": [
        { "signal": "died", "target": ".", "method": "_on_player_died" }
      ]
    },
    {
      "name": "CollisionShape2D",
      "type": "CollisionShape2D",
      "parent": "./Player",
      "properties": {
        "shape": "sub_resource(\"sub_1\")"
      }
    }
  ]
}
```

### Schema Rules

| Field | Type | Notes |
|-------|------|-------|
| `header.godot_version` | `str` | E.g. `"4.2"`. Read from file, passthrough on write. |
| `header.scene_format` | `int` | Always `3` for Godot 4.x. |
| `resources[].type` | `str` | `"ext_resource"` or `"sub_resource"` only. |
| `resources[].id` | `str` | String representation of the integer ID. |
| `resources[].uid` | `str\|null` | Omitted on create (Godot assigns). Preserved on read. |
| `resources[].properties` | `dict` | sub_resource properties. Keys are property names, values are TSCN-format strings. |
| `nodes[].name` | `str` | Node name. May contain `/` only if escaped as `\\/`. |
| `nodes[].type` | `str` | Godot class name (e.g. `"Node2D"`, `"Sprite2D"`). |
| `nodes[].parent` | `str\|null` | `null` = root node. Otherwise a path: `"."` for direct child of root, `"./Child"` for nested. |
| `nodes[].properties` | `dict` | Key-value pairs. Values are TSCN-format strings: `"Vector2(1,2)"`, `"Color(1,0,0)"`, `"ext_resource(\"1\")"`, `"Color(1, 1, 1, 1)"`. |
| `nodes[].groups` | `list[str]` | Empty list if no groups. |
| `nodes[].connections` | `list[dict]` | Each: `{signal, target, method}`. Target is a node path relative to root. |

---

## Requirements

### R1: read_scene

The system MUST parse a `.tscn` file and return its contents as the JSON schema above.

**Acceptance Criteria:**

- AC-1.1: Given a `.tscn` with 1 root node and 0 children, `read_scene` returns JSON with exactly 1 node where `parent` is `null`.
- AC-1.2: Given a `.tscn` with `ext_resource` and `sub_resource` entries, the `resources` array contains both with correct `id`, `path`, `resource_type`, and `properties`.
- AC-1.3: Given a `.tscn` with signal connections (`[connection signal="died" from="Player" to="." method="_on_player_died"]`), each node's `connections` array contains the correct `{signal, target, method}`.
- AC-1.4: Given a `.tscn` with node groups (`groups=["player", "enemies"]`), the `groups` field is populated.
- AC-1.5: Given a `.tscn` that does not exist, the tool returns `"ERROR: Scene file not found: {path}"`.
- AC-1.6: Given a `.tscn` with `uid` fields on resources, the UIDs are preserved in the JSON output.
- AC-1.7: The output is valid JSON parseable by `json.loads()`.

---

### R2: create_scene

The system MUST accept a JSON definition and produce a valid `.tscn` file that Godot 4.x opens without parse errors.

**Acceptance Criteria:**

- AC-2.1: Given a JSON with 1 root node (type `Node2D`) and no children, the tool writes a `.tscn` file with a `[gd_scene]` header and a `[node name="Root" type="Node2D"]` block.
- AC-2.2: Given a JSON with `ext_resource` entries, the output file contains matching `[ext_resource]` lines with correct `id`, `path`, and `type`.
- AC-2.3: Given a JSON with `sub_resource` entries, the output file contains matching `[sub_resource]` lines with correct properties.
- AC-2.4: Given a JSON with nested nodes (`parent: "./Child"`), the output `.tscn` has correct `parent` attributes.
- AC-2.5: Given a JSON with signal connections, the output file contains `[connection]` lines with correct `signal`, `from`, `to`, and `method`.
- AC-2.6: The file is written at the path specified by `file_path`, relative to `GODOT_PROJECT`.
- AC-2.7: On success, the tool returns `"OK: Created scene {file_path} ({N} nodes, {M} resources)"`.
- AC-2.8: Given an empty nodes list, the tool returns `"ERROR: Scene must contain at least one node (root)"`.

---

### R3: modify_scene

The system MUST apply surgical modifications to an existing `.tscn` file. Supports add/remove nodes, set properties, and connect/disconnect signals.

**Acceptance Criteria:**

- AC-3.1: `add_node` appends a node to the node list. The new node appears in the output `read_scene` after modification.
- AC-3.2: `remove_node` removes the specified node AND all its descendants (child nodes whose `parent` path starts with the removed node's path).
- AC-3.3: `set_property` updates a property value on a specific node. The change persists in the `.tscn` file.
- AC-3.4: `connect_signal` adds a connection entry. `disconnect_signal` removes it.
- AC-3.5: `add_node` with a `parent` path referencing a non-existent node returns `"ERROR: Parent node not found: {parent}"`.
- AC-3.6: `remove_node` on the root node returns `"ERROR: Cannot remove root node"`.
- AC-3.7: `modify_scene` on a non-existent file returns `"ERROR: Scene file not found: {path}"`.
- AC-3.8: Multiple operations in a single call are applied in order (add, then set_property, then connect).
- AC-3.9: On success, the tool returns `"OK: Modified scene {file_path} — {summary of changes}"`.

---

### R4: Path Security

All three tools MUST enforce path security to prevent directory traversal outside `GODOT_PROJECT`.

**Acceptance Criteria:**

- AC-4.1: Any `file_path` resolving outside `GODOT_PROJECT` returns `"ERROR: Path traversal detected. '{file_path}' escapes the project root."`.
- AC-4.2: `read_scene("../../../etc/passwd")` is rejected.
- AC-4.3: `create_scene` with `file_path` containing `..` segments that escape the project root is rejected.
- AC-4.4: `modify_scene` with a path escaping the project root is rejected.
- AC-4.5: Paths with `..` that stay inside `GODOT_PROJECT` (e.g. `"../project_dir/scene.tscn"` if that resolves inside) are allowed.

---

### R5: Error Handling

All tools MUST return `str` and follow the existing error pattern: `"ERROR: {message}"`.

**Acceptance Criteria:**

- AC-5.1: All errors start with `"ERROR:"`.
- AC-5.2: No exceptions propagate to the caller — all are caught and returned as error strings.
- AC-5.3: `json.loads()` on a `read_scene` result never raises `json.JSONDecodeError` — the result is either valid JSON or an `ERROR:` string.
- AC-5.4: `godot-parser` import failures are caught at module load and surface as `"ERROR: godot-parser not installed. Run: pip install godot-parser"` in tool responses.

---

### R6: godot-parser Integration

`SceneBuilder` wraps `godot-parser` and mediates all access.

**Acceptance Criteria:**

- AC-6.1: `SceneBuilder.__init__` accepts `project_dir: Path`.
- AC-6.2: `SceneBuilder.read(file_path) -> dict` returns the JSON schema dict.
- AC-6.3: `SceneBuilder.write(file_path, scene_data) -> None` writes a `.tscn` from the JSON dict.
- AC-6.4: `SceneBuilder.modify(file_path, operations) -> dict` applies ops and returns the updated scene dict.
- AC-6.5: `godot-parser` is imported lazily with a try/except so the MCP server starts even if it's missing.
- AC-6.6: Properties are stored as TSCN-format strings (e.g. `"Vector2(100, 200)"`), not parsed Python objects.

---

## Edge Cases

| Case | Behavior |
|------|----------|
| Empty scene (root only, no children) | Valid. `nodes` has 1 entry. |
| Node named `.` | Rejected. `.` is reserved as parent-path separator. |
| Circular parent references | Not possible — parent is a string path, not a node reference. `add_node` validates parent exists. |
| Very large scene (1000+ nodes) | No explicit limit. `godot-parser` handles it. JSON output may be large but that's the caller's concern. |
| File encoding other than UTF-8 | `godot-parser` handles encoding. We pass through its behavior. |
| Missing ext_resource file | Preserved in JSON as-is. Godot itself shows a "missing resource" warning. We don't validate. |
| Duplicate node names | Allowed. Godot handles this with path disambiguation. |
| `uid` fields | Preserved on read, omitted on create. Godot assigns on first open. |

---

## File Locations

| File | Action | Purpose |
|------|--------|---------|
| `core/scene_builder.py` | Create | `SceneBuilder` class |
| `core/mcp_server.py` | Modify | 3 new `@mcp.tool()` + input models |
| `tests/test_scene_builder.py` | Create | Unit tests for SceneBuilder |
| `tests/test_mcp_scene_tools.py` | Create | Integration tests for MCP tools |
| `tests/conftest.py` | Modify | Sample `.tscn` fixtures |
| `pyproject.toml` | Modify | Add `godot-parser` to dependencies |

---

## Test Fixtures

`tests/conftest.py` should provide:

- `sample_scene_minimal` — Root Node2D, no children, no resources.
- `sample_scene_complex` — Root + children + ext_resource + sub_resource + connections + groups.
- `sample_scene_nested` — 3-level hierarchy testing deep parent paths.
