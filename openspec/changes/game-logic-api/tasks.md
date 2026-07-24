# Tasks: Game Logic API

## Task 1: ScriptBuilder Foundation + Path Validation
**Description**: Create `core/script_builder.py` with ScriptBuilder class, `__init__`, and `_validate_path()` method. Identical to SceneBuilder's path validation.
**Files**: `core/script_builder.py` (NEW)
**Tests**: Path traversal rejection tests (same as SceneBuilder)
**Acceptance Criteria**: 
- ScriptBuilder class exists with project_dir attribute
- `_validate_path()` rejects traversal attempts
- Returns `Path | str` (error string on failure)
**Estimated Lines**: ~50

## Task 2: create() — Basic Script Generation
**Description**: Implement `create()` method with template-based GDScript generation. Support extends, class_name, signals, variables (exported + regular), functions with body.
**Files**: `core/script_builder.py`
**Tests**: Test create with full definition, verify output contains all elements in correct order
**Acceptance Criteria**:
- Creates valid .gd file from definition dict
- Correct section order: extends → class_name → signals → vars → functions
- Tab indentation throughout
- Returns "OK: ..." message with counts
**Estimated Lines**: ~120

## Task 3: read() — Basic Script Parsing
**Description**: Implement `read()` method with regex-based parsing. Extract extends, class_name, signals, variables, functions with bodies.
**Files**: `core/script_builder.py`
**Tests**: Test read with hand-crafted .gd fixtures, verify dict output
**Acceptance Criteria**:
- Parses extends, class_name, signals, variables, functions
- Function bodies captured as line lists
- Returns structured dict matching create's input schema
- Returns "ERROR: ..." on file not found
**Estimated Lines**: ~100

## Task 4: modify() — Operation List
**Description**: Implement `modify()` method with 9 operation types: add/remove signal, add/remove variable, add/remove function, replace_function_body, set_extends, set_class_name.
**Files**: `core/script_builder.py`
**Tests**: Test each operation type individually, test multi-op order
**Acceptance Criteria**:
- All 9 operation types work correctly
- Operations applied in order
- Unknown action returns "ERROR: Unknown action: ..."
- Returns "OK: ..." with change summary
**Estimated Lines**: ~150

## Task 5: MCP Tool Registration
**Description**: Add 3 new `@mcp.tool()` registrations and 3 Pydantic input models in `core/mcp_server.py`.
**Files**: `core/mcp_server.py` (MODIFY)
**Tests**: Test tool registration, test delegation to ScriptBuilder
**Acceptance Criteria**:
- 3 new tools registered: create_script, read_script, modify_script
- 3 Pydantic input models: CreateScriptInput, ReadScriptInput, ModifyScriptInput
- Tools delegate to ScriptBuilder methods
- Exceptions caught and returned as "ERROR: ..."
**Estimated Lines**: ~60

## Task 6: Integration Tests + Round-trip
**Description**: Write integration tests: create → read → compare structure. Test with real .gd files in test_project/.
**Files**: `tests/test_script_builder.py`
**Tests**: Round-trip test, edge cases (empty body, no extends, nested indents)
**Acceptance Criteria**:
- Round-trip: create → read produces equivalent structure
- Edge cases handled correctly
- 80%+ coverage for core/script_builder.py
**Estimated Lines**: ~150

---

**Total Estimated**: ~630 lines
**Dependency Order**: 1 → 2 → 3 → 4 → 5 → 6
