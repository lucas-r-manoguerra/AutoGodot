# Tasks: Scene Builder (.tscn) — 3-Tool MVP

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 430–490 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | SceneBuilder class + dep + fixtures | PR 1 (~185 lines) | `pytest tests/test_scene_builder.py -m "read or create"` | N/A — unit tests with mocked godot-parser; no runtime scenario | `core/scene_builder.py`, `pyproject.toml`, `tests/conftest.py` |
| 2 | MCP tool registrations + input models | PR 2 (~70 lines) | `pytest tests/test_scene_builder.py -m "mcp"` | N/A — verifies tool function wiring, no real Godot needed | `core/mcp_server.py` changes only |
| 3 | Full test suite + edge cases | PR 3 (~195 lines) | `pytest tests/test_scene_builder.py -v` | N/A — comprehensive mocked tests; round-trip and error paths | `tests/test_scene_builder.py` additions |

## Phase 1: Foundation

- [x] 1.1 Add `godot-parser>=0.1.7` to `pyproject.toml` `[project.dependencies]`. Verify: `pip install -e ".[dev]"` succeeds.
- [x] 1.2 Create `core/scene_builder.py` with lazy import guard (try/except → sentinel) and `SceneBuilder.__init__(project_dir: Path)`. Verify: `python -c "from core.scene_builder import SceneBuilder"` with missing godot-parser shows sentinel error.
- [x] 1.3 Implement `SceneBuilder.read(scene_path) -> dict`: path traversal check, `godot_parser.load()`, flatten tree via `_flatten_tree()`, build JSON schema with header/resources/nodes/connections/groups. Verify: write sample `.tscn` fixture to tmp, call `read`, assert dict matches schema.
- [x] 1.4 Implement `SceneBuilder.create(scene_path, definition) -> str`: path traversal check, build `GDScene()`, add ext/sub resources, build node tree via `use_tree()`, call `scene.write()`, return OK message with node/resource counts. Verify: create scene from minimal JSON, read it back, assert nodes match.
- [x] 1.5 Implement `SceneBuilder.modify(scene_path, operations) -> str`: path traversal check, load scene, apply operations in order (add_node, remove_node, set_property, connect_signal, disconnect_signal), write back, return OK with change summary. Verify: create scene, modify with add_node, read back, assert new node present.

## Phase 2: MCP Integration

- [ ] 2.1 Add input models to `core/mcp_server.py`: `NodeDefinition`, `ResourceRef`, `SceneDefinition`, `ModifyOperation`, `ReadSceneInput`, `CreateSceneInput`, `ModifySceneInput` (Pydantic BaseModel). Verify: import succeeds, `ReadSceneInput(scene_path="x.tscn")` validates.
- [ ] 2.2 Add lazy singleton for `SceneBuilder` in `mcp_server.py` (same pattern as `godot`/`vision`), add 3 `@mcp.tool()` functions: `read_scene`, `create_scene`, `modify_scene` with docstrings and try/except → `"ERROR: ..."` wrapping. Verify: `mcp.list_tools()` returns 6 tools (3 existing + 3 new).

## Phase 3: Testing

- [x] 3.1 Add to `tests/conftest.py`: `SAMPLE_TSCN` constant (format=3, ext_resource, sub_resource, nested nodes, connections, groups), `sample_tscn` fixture writing it to tmp_path, `scene_builder` fixture returning `SceneBuilder(tmp_godot_project)`. Verify: `pytest tests/ --collect-only` shows new fixtures.
- [ ] 3.2 Write read_scene tests: AC-1.1 (root-only), AC-1.2 (resources), AC-1.3 (connections), AC-1.4 (groups), AC-1.5 (file not found → ERROR), AC-1.6 (UID preserved), AC-1.7 (valid JSON). Verify: `pytest tests/test_scene_builder.py -m "read" -v`.
- [ ] 3.3 Write create_scene tests: AC-2.1 (root node), AC-2.2 (ext_resource), AC-2.3 (sub_resource), AC-2.4 (nested parent), AC-2.5 (connections), AC-2.6 (file at path), AC-2.7 (OK message format), AC-2.8 (empty nodes → ERROR). Verify: `pytest tests/test_scene_builder.py -m "create" -v`.
- [ ] 3.4 Write modify_scene tests: AC-3.1 (add_node), AC-3.2 (remove_node + descendants), AC-3.3 (set_property), AC-3.4 (connect/disconnect_signal), AC-3.5 (bad parent → ERROR), AC-3.6 (remove root → ERROR), AC-3.7 (file not found → ERROR), AC-3.8 (multi-op order), AC-3.9 (OK summary). Verify: `pytest tests/test_scene_builder.py -m "modify" -v`.
- [ ] 3.5 Write path security tests (R4): AC-4.1–AC-4.5 for all 3 tools with `../../etc/passwd`, escaping paths, and valid `..` paths. Verify: `pytest tests/test_scene_builder.py -m "security" -v`.
- [ ] 3.6 Write error handling tests (R5): AC-5.1 (ERROR prefix), AC-5.2 (no exceptions propagate), AC-5.3 (json.loads never raises on read_scene), AC-5.4 (missing godot-parser → helpful error). Verify: `pytest tests/test_scene_builder.py -m "error" -v`.
- [ ] 3.7 Write integration test: create_scene → read_scene round-trip comparing node names, types, parent paths, and property values. Verify: `pytest tests/test_scene_builder.py -m "integration" -v`.
- [ ] 3.8 Run full suite: `pytest tests/ -v --tb=short`. Verify all 21 existing tests still pass plus new tests.

## Dependency Graph

```
1.1 ──→ 1.2 ──→ 1.3 ──→ 1.4 ──→ 1.5
                                  ↓
                               2.1 ──→ 2.2
                                  ↓
                               3.1 ──→ 3.2, 3.3, 3.4 (parallel)
                                        3.5, 3.6     (parallel)
                                        3.7          (after 3.2–3.6)
                                        3.8          (final gate)
```

## Critical Path

`1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 2.1 → 2.2 → 3.1 → 3.2–3.6 → 3.7 → 3.8`

The SceneBuilder class (Phase 1) is the foundation — everything depends on it. MCP integration (Phase 2) depends on SceneBuilder being complete. Testing (Phase 3) depends on both, but fixture setup (3.1) gates all test tasks.
