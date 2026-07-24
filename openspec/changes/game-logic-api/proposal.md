# Proposal: Game Logic API

## Intent

GDScript files (.gd) are currently only writable as raw text via `write_game_file`. LLMs must construct complete GDScript strings manually — no structured creation, parsing, or surgical modification exists. This makes it error-prone to generate correct GDScript, impossible to inspect existing scripts programmatically, and fragile to modify specific functions/signals without rewriting the entire file. The SceneBuilder pattern proves structured manipulation works for `.tscn`; this extends the same approach to `.gd`.

## Scope

### In Scope
- `create_script`: Build a `.gd` file from structured JSON (extends, class_name, signals, variables, functions)
- `read_script`: Parse a `.gd` file into structured JSON via regex/template (no external parser)
- `modify_script`: Apply surgical operations (add/remove/replace function, add/remove signal, add/remove variable, set metadata)
- Pydantic input models for all 3 tools
- `ScriptBuilder` class in `core/script_builder.py` following the SceneBuilder pattern
- 3 new `@mcp.tool()` registrations in `core/mcp_server.py`
- Strict TDD with 80%+ coverage for new code

### Out of Scope
- GDScript type inference or semantic analysis
- Multi-file refactoring or cross-script dependency resolution
- GDScript syntax validation (Godot itself does this)
- Inner classes or anonymous functions
- Comment/formatting preservation in read → modify round-trips

## Capabilities

### New Capabilities
- `script-builder`: Structured CRUD for GDScript files — create from JSON, parse to JSON, surgical modify

### Modified Capabilities
None — this is additive. `write_game_file` remains for raw text when structured manipulation isn't needed.

## Approach

New `ScriptBuilder` class (`core/script_builder.py`) mirroring `SceneBuilder`:
- **create**: Template-based GDScript generation from a Pydantic-validated definition dict. Tab indentation. Sections ordered: extends → class_name → signals → @export vars → vars → functions.
- **read**: Regex-based parsing of extends, class_name, signal, var, and func declarations. Function bodies captured as line lists. No external parser.
- **modify**: Operation list pattern (add_signal, remove_signal, add_variable, remove_variable, add_function, remove_function, replace_function_body, set_extends, set_class_name). Load → mutate → serialize.
- Path validation via `_validate_path()` (same as SceneBuilder).
- 3 Pydantic input models in `mcp_server.py`: `CreateScriptInput`, `ReadScriptInput`, `ModifyScriptInput`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `core/script_builder.py` | New | ScriptBuilder class + Pydantic models |
| `core/mcp_server.py` | Modified | 3 new `@mcp.tool()` + 3 input models |
| `tests/test_script_builder.py` | New | TDD test suite |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Regex parsing misses edge cases (nested parens, multiline bodies) | Medium | Scope v1 to simple flat functions; document limitations |
| Generated GDScript has subtle syntax errors | Low | Round-trip tests: create → read → compare structure |
| Tab vs space indentation mismatch | Low | Enforce `\t` everywhere in template; test explicitly |

## Rollback Plan

Revert 3 files: delete `core/script_builder.py`, remove 3 tool registrations + 3 input models from `core/mcp_server.py`, delete `tests/test_script_builder.py`. No database, no migration, no data loss.

## Dependencies

- Pydantic (already installed)
- No new external dependencies

## Success Criteria

- [ ] `create_script` produces valid GDScript from JSON for all GDScript constructs in the JSON schema
- [ ] `read_script` correctly parses extends, class_name, signals, variables, and functions
- [ ] `modify_script` applies each operation type without corrupting the rest of the file
- [ ] Round-trip: create → read produces equivalent structure
- [ ] 80%+ line coverage for `core/script_builder.py`
- [ ] Path traversal rejected for all 3 tools
- [ ] All errors return `"ERROR: ..."` strings (no exceptions leak)
