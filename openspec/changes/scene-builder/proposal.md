# Proposal: Scene Builder (.tscn) — 3-Tool MVP

## Intent

AI agents can write raw `.tscn` text via `write_game_file`, but cannot parse existing scenes or manipulate scene trees structurally. Scene Builder adds structured scene understanding and creation.

## Scope

### In Scope
- `read_scene` — parse `.tscn` → structured JSON (nodes, resources, connections)
- `create_scene` — structured JSON definition → valid `.tscn` file
- `modify_scene` — surgical edits (add/remove nodes, set properties, connect signals)
- `.tscn` format=3, ext_resource/sub_resource, signal connections, basic `.tres`

### Out of Scope
- Scene inheritance, animations, 3D meshes, TileMap, UIDs, real-time editor sync, binary formats

## Capabilities

### New Capabilities
- `scene-builder`: Parse, create, and modify Godot .tscn scene files via structured JSON

### Modified Capabilities
- None

## Approach

**Dependency:** `godot-parser` (stevearc, MIT) for parsing and writing.

**Module structure:**
```
core/scene_builder.py        — SceneBuilder class wrapping godot-parser
core/mcp_server.py           — 3 new @mcp.tool() registrations + input models
tests/test_scene_builder.py  — Unit tests
pyproject.toml               — Add godot-parser dependency
```

**Key decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scene tree JSON | Flat node list with `parent` path | Direct mapping to TSCN parent= attribute |
| Property values | String (`"Vector2(100, 200)"`) | Matches TSCN format, no type inference |
| Error handling | `try/except` → `"ERROR: ..."` string | Matches existing tool pattern |
| File paths | Relative to `GODOT_PROJECT`, traversal check | Same security as write_game_file |
| UIDs | Skip — Godot assigns on first open | Avoids generation complexity |
| Return type | `str` (JSON for reads, confirmation for writes) | Consistent with existing tools |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `core/scene_builder.py` | New | SceneBuilder class |
| `core/mcp_server.py` | Modified | 3 new tool registrations |
| `tests/test_scene_builder.py` | New | Unit tests |
| `tests/conftest.py` | Modified | Sample .tscn fixtures |
| `pyproject.toml` | Modified | Add godot-parser |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| godot-parser lacks format=3 UID support | Medium | Omit UIDs; Godot assigns on open |
| Exotic Godot value types | Low | godot-parser handles most; defer edge cases |
| Scene inheritance unsupported | Known | Documented as OUT scope |

## Rollback Plan

Remove `core/scene_builder.py`, 3 tool registrations, `godot-parser` dep, and test file. Existing `write_game_file` unaffected.

## Success Criteria

- [ ] `read_scene` parses real Godot 4.x `.tscn` accurately
- [ ] `create_scene` produces `.tscn` Godot opens without errors
- [ ] `modify_scene` adds nodes and sets properties on existing scenes
- [ ] All 21 existing tests pass; new tests cover all 3 tools
- [ ] Path traversal protection on all scene operations
