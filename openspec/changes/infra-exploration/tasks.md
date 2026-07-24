# AutoGodot Infrastructure Tasks

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated total changed lines | ~650 |
| New files | 9 |
| Modified files | 4 |
| Chained PRs recommended | **Yes** |
| 400-line budget risk | **High** |

**Recommendation**: Split into 2 chained PRs:
- **PR1**: Testing foundation + tool config (~350 lines)
- **PR2**: CI/CD + pre-commit + type annotations (~300 lines)

---

## Task List

### Task 1: Create pyproject.toml with tool configurations
- **File(s)**: `pyproject.toml` (new)
- **Lines**: ~120
- **Dependencies**: none
- **Description**: Create pyproject.toml with:
  - Project metadata (name, version, description, python requires)
  - Dependencies from requirements.txt
  - Optional dev dependencies (pytest, ruff, black, mypy, pre-commit)
  - Ruff configuration (target-version, line-length, select/ignore rules)
  - Black configuration (target-version, line-length)
  - Mypy configuration (python_version, warn_return_any, per-module overrides)
  - Pytest configuration (testpaths, asyncio_mode, markers)
  - Coverage configuration (source, omit, fail_under=80)
- **Verification**: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"` succeeds

### Task 2: Create tests/ directory structure
- **File(s)**: `tests/__init__.py` (new)
- **Lines**: 1
- **Dependencies**: Task 1
- **Description**: Create empty `tests/__init__.py` to make tests a package
- **Verification**: `python -c "import tests"` succeeds

### Task 3: Create shared test fixtures (conftest.py)
- **File(s)**: `tests/conftest.py` (new)
- **Lines**: ~80
- **Dependencies**: Task 2
- **Description**: Create conftest.py with:
  - `tmp_godot_project` fixture (creates temp dir with project.godot)
  - `godot_controller` fixture (creates GodotController with temp project)
  - `vision_qa` fixture (creates VisionQA instance)
  - `mock_subprocess` fixture (mocks asyncio.create_subprocess_exec)
  - `mock_screen_capture` fixture (mocks mss and PIL)
- **Verification**: `pytest --collect-only` discovers fixtures

### Task 4: Create GodotController tests
- **File(s)**: `tests/test_godot_controller.py` (new)
- **Lines**: ~120
- **Dependencies**: Task 3
- **Description**: Create test_godot_controller.py with:
  - `test_run_project_success` — mock subprocess returns (b"out", b"err"), verify dict structure
  - `test_run_project_timeout` — mock subprocess hangs, verify timeout handling and process kill
  - `test_run_project_file_not_found` — mock FileNotFoundError, verify error dict
  - `test_run_project_custom_args` — verify extra_args passed to subprocess
  - `test_build_command_with_scene` — verify --scene flag added
  - `test_build_command_without_scene` — verify no --scene flag
  - `test_path_resolution` — verify project_dir is resolved
- **Verification**: `pytest tests/test_godot_controller.py -v` passes

### Task 5: Create VisionQA tests
- **File(s)**: `tests/test_vision_qa.py` (new)
- **Lines**: ~100
- **Dependencies**: Task 3
- **Description**: Create test_vision_qa.py with:
  - `test_capture_screen_success` — mock mss/PIL, verify base64 output
  - `test_capture_screen_resize` — verify aspect ratio preserved
  - `test_capture_screen_no_mss` — verify RuntimeError when mss missing
  - `test_capture_screen_no_pillow` — verify RuntimeError when Pillow missing
  - `test_capture_screen_quality` — verify JPEG quality parameter respected
- **Verification**: `pytest tests/test_vision_qa.py -v` passes

### Task 6: Create MCP server tests
- **File(s)**: `tests/test_mcp_server.py` (new)
- **Lines**: ~100
- **Dependencies**: Task 3
- **Description**: Create test_mcp_server.py with:
  - `test_write_game_file_registration` — verify tool is registered
  - `test_run_godot_test_registration` — verify tool is registered
  - `test_capture_game_screen_registration` — verify tool is registered
  - `test_path_traversal_protection` — verify "../../etc/passwd" blocked
  - `test_write_game_file_success` — verify file written to temp project
  - `test_write_game_file_creates_dirs` — verify create_dirs=True works
- **Verification**: `pytest tests/test_mcp_server.py -v` passes

### Task 7: Run full test suite and verify coverage
- **File(s)**: none (validation only)
- **Lines**: 0
- **Dependencies**: Tasks 4, 5, 6
- **Description**: Run `pytest --cov=core --cov-report=term-missing` and verify:
  - All tests pass
  - Coverage ≥80% for core/*.py
  - No regressions in existing functionality
- **Verification**: Exit code 0, coverage report shows ≥80%

### Task 8: Add type annotations to core modules
- **File(s)**: `core/godot_controller.py`, `core/mcp_server.py`, `core/vision_qa.py` (modify)
- **Lines**: ~50 (annotations only, no logic changes)
- **Dependencies**: Task 1 (mypy config)
- **Description**: Add explicit type annotations:
  - GodotController.run_project() return type → `dict[str, Any]`
  - GodotController._build_command() return type → `list[str]`
  - VisionQA.capture_screen() return type → `dict[str, Any]`
  - All Pydantic model fields already typed (verify)
  - Add `from __future__ import annotations` where missing
- **Verification**: `mypy core/` passes with zero errors

### Task 9: Create GitHub Actions CI workflow
- **File(s)**: `.github/workflows/ci.yml` (new)
- **Lines**: ~80
- **Dependencies**: Tasks 1, 7
- **Description**: Create ci.yml with:
  - Trigger: pull_request and push to main/master
  - Jobs (all parallel):
    - lint: ruff check core/ tests/
    - format: black --check core/ tests/
    - typecheck: mypy core/
    - test: pytest with matrix (Python 3.10, 3.11)
  - Cache pip dependencies
  - Upload coverage artifact on Python 3.10
- **Verification**: `act -l` (if act installed) or manual review of YAML syntax

### Task 10: Create pre-commit configuration
- **File(s)**: `.pre-commit-config.yaml` (new)
- **Lines**: ~25
- **Dependencies**: Task 1
- **Description**: Create .pre-commit-config.yaml with:
  - ruff hook (lint + format)
  - black hook (formatting)
  - mypy hook (type checking)
  - Pin versions to latest stable
- **Verification**: `pre-commit run --all-files` passes

### Task 11: Update requirements.txt with dev dependencies
- **File(s)**: `requirements.txt` (modify)
- **Lines**: ~10
- **Dependencies**: Task 1
- **Description**: Add comment section for dev dependencies:
  ```txt
  # Dev dependencies (install with: pip install -r requirements.txt -r requirements-dev.txt)
  # Or install all: pip install -e ".[dev]"
  ```
- **Verification**: `pip install -e ".[dev]"` succeeds

### Task 12: Final validation
- **File(s)**: none (validation only)
- **Lines**: 0
- **Dependencies**: All previous tasks
- **Description**: Run full validation suite:
  - `pytest --cov=core --cov-report=term-missing` — all tests pass, coverage ≥80%
  - `ruff check core/ tests/` — zero errors
  - `black --check core/ tests/` — no changes needed
  - `mypy core/` — zero errors
  - `pre-commit run --all-files` — all hooks pass
- **Verification**: All commands exit with code 0

---

## Dependency Graph

```
Task 1 (pyproject.toml)
  ├── Task 2 (tests/__init__.py)
  │     └── Task 3 (conftest.py)
  │           ├── Task 4 (test_godot_controller.py)
  │           ├── Task 5 (test_vision_qa.py)
  │           └── Task 6 (test_mcp_server.py)
  │                 └── Task 7 (run tests + coverage)
  ├── Task 8 (type annotations)
  ├── Task 10 (pre-commit config)
  └── Task 11 (requirements.txt update)
        └── Task 9 (CI workflow)
              └── Task 12 (final validation)
```

---

## Critical Path

```
Task 1 → Task 2 → Task 3 → Task 4/5/6 → Task 7 → Task 9 → Task 12
```

**Estimated total time**: ~2-3 hours for a single developer

---

## PR Split Strategy

### PR1: Testing Foundation (~350 lines)
- Tasks 1-7
- Creates pyproject.toml, test suite, fixtures
- Verifiable: `pytest` passes with coverage

### PR2: Code Quality + CI/CD (~300 lines)
- Tasks 8-12
- Adds type annotations, CI workflow, pre-commit
- Verifiable: `ruff check`, `black --check`, `mypy`, `pre-commit run` all pass
