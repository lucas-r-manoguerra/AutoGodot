# AutoGodot Infrastructure Spec

## Overview

Add comprehensive testing, CI/CD, linting, formatting, type checking, and pre-commit hooks to AutoGodot. The project currently has zero tests, no automated quality gates, and no code quality tooling. This spec establishes a production-grade infrastructure foundation while preserving all existing functionality, documentation, and setup scripts.

---

## Requirements

### R1: Testing Foundation
**Priority**: Critical
**Description**: Establish pytest-based test suite with mocks for external dependencies (Godot subprocess, screen capture).

**Scenarios**:

- **S1.1**: `pytest` runs successfully from project root and discovers all test files
  - Given: tests/ directory exists with test files
  - When: `pytest` is executed
  - Then: all tests are discovered and executed, exit code 0 on success

- **S1.2**: GodotController is testable without Godot installed
  - Given: tests/test_godot_controller.py exists
  - When: tests mock `asyncio.create_subprocess_exec`
  - Then: run_project() returns expected dict structure with stdout, stderr, returncode, duration, timed_out

- **S1.3**: VisionQA is testable without screen hardware
  - Given: tests/test_vision_qa.py exists
  - When: tests mock `mss.mss()` and `PIL.Image`
  - Then: capture_screen() returns dict with base64, width, height, format

- **S1.4**: MCP server tool registration is validated
  - Given: tests/test_mcp_server.py exists
  - When: tools are registered via @mcp.tool()
  - Then: write_game_file, run_godot_test, capture_game_screen are all registered

- **S1.5**: Path traversal protection is tested
  - Given: write_game_file receives `../../etc/passwd` as file_path
  - When: the tool is called
  - Then: returns ERROR message about path traversal, no file is written

- **S1.6**: Timeout enforcement is tested
  - Given: GodotController.run_project() is called with timeout=1.0
  - When: subprocess exceeds timeout
  - Then: process is killed, timed_out=True in result

- **S1.7**: Test coverage reaches ≥80% for core modules
  - Given: `pytest --cov=core --cov-report=term-missing` is run
  - Then: coverage for core/*.py is ≥80%

---

### R2: Code Quality Tools (Linting + Formatting)
**Priority**: High
**Description**: Add ruff for linting and black for formatting with consistent configuration.

**Scenarios**:

- **S2.1**: `ruff check` passes with zero errors
  - Given: ruff is configured in pyproject.toml
  - When: `ruff check core/ tests/` is run
  - Then: exit code 0, no errors reported

- **S2.2**: `black --check` passes with no formatting changes needed
  - Given: black is configured in pyproject.toml
  - When: `black --check core/ tests/` is run
  - Then: exit code 0, all files are properly formatted

- **S2.3**: `ruff format` produces consistent output
  - Given: code has mixed string formatting (%-formatting and f-strings)
  - When: `ruff format core/` is run
  - Then: consistent style across all files, no functional changes

- **S2.4**: Configuration is centralized in pyproject.toml
  - Given: pyproject.toml exists at project root
  - When: ruff and black settings are read
  - Then: both tools use configuration from pyproject.toml, no separate config files needed

---

### R3: Type Checking
**Priority**: Medium
**Description**: Add mypy for static type checking with gradual strictness.

**Scenarios**:

- **S3.1**: `mypy core/` passes without errors
  - Given: mypy is configured in pyproject.toml
  - When: `mypy core/` is run
  - Then: exit code 0, no type errors

- **S3.2**: Pydantic models are fully typed
  - Given: WriteGameFileInput, RunGodotTestInput, CaptureGameScreenInput exist
  - When: mypy checks these classes
  - Then: all fields have explicit types, no `Any` usage

- **S3.3**: Return types are annotated on all public functions
  - Given: GodotController.run_project(), VisionQA.capture_screen() exist
  - When: mypy checks these functions
  - Then: return types are explicit (dict[str, Any] or specific TypedDict)

---

### R4: CI/CD Pipeline
**Priority**: High
**Description**: GitHub Actions workflow that runs lint, format, type check, and tests on every PR.

**Scenarios**:

- **S4.1**: CI workflow triggers on pull requests
  - Given: .github/workflows/ci.yml exists
  - When: a PR is opened or updated
  - Then: workflow runs automatically

- **S4.2**: Lint job runs ruff check
  - Given: CI workflow is triggered
  - When: lint job executes
  - Then: `ruff check core/ tests/` runs and fails if errors found

- **S4.3**: Format job runs black check
  - Given: CI workflow is triggered
  - When: format job executes
  - Then: `black --check core/ tests/` runs and fails if unformatted code found

- **S4.4**: Type check job runs mypy
  - Given: CI workflow is triggered
  - When: typecheck job executes
  - Then: `mypy core/` runs and fails if type errors found

- **S4.5**: Test job runs pytest with coverage
  - Given: CI workflow is triggered
  - When: test job executes
  - Then: `pytest --cov=core --cov-report=term-missing` runs and fails if tests fail or coverage <80%

- **S4.6**: All jobs run in parallel for speed
  - Given: CI workflow has lint, format, typecheck, test jobs
  - When: workflow runs
  - Then: all 4 jobs execute in parallel (not sequential)

- **S4.7**: Python version matrix is tested
  - Given: CI workflow is configured
  - When: test job runs
  - Then: tests pass on Python 3.10 and 3.11 (minimum supported)

---

### R5: Pre-commit Hooks
**Priority**: Medium
**Description**: Local pre-commit hooks that run lint, format, and type check before commit.

**Scenarios**:

- **S5.1**: Pre-commit hooks are installed via `pre-commit install`
  - Given: .pre-commit-config.yaml exists
  - When: `pre-commit install` is run
  - Then: .git/hooks/pre-commit is created and executable

- **S5.2**: Hooks run automatically on `git commit`
  - Given: pre-commit hooks are installed
  - When: `git commit` is executed
  - Then: ruff check, black --check, and mypy run automatically

- **S5.3**: Commit is blocked if hooks fail
  - Given: code has lint errors
  - When: `git commit` is executed
  - Then: commit is blocked, errors are displayed, user can fix and re-commit

- **S5.4**: Hooks skip on `--no-verify` (emergency bypass)
  - Given: pre-commit hooks are installed
  - When: `git commit --no-verify` is executed
  - Then: hooks are skipped, commit proceeds

---

## Constraints

1. **Do NOT modify** existing documentation in `docs/` — preserve all 8 files as-is
2. **Do NOT modify** `scripts/setup_and_run.sh` — it's production-ready
3. **Do NOT modify** `.gitignore` — already comprehensive
4. **Do NOT modify** `config/` — example config is fine
5. **Preserve** all existing MCP tool behavior — tests must validate current functionality
6. **Preserve** Python 3.10+ compatibility — no f-string without quotes, no walrus operator abuse
7. **Preserve** async/await patterns — all tool functions are async

---

## Dependencies

```
Phase 1: Testing Foundation (R1)
    ↓
Phase 2: Code Quality (R2) + Type Checking (R3) — can run in parallel
    ↓
Phase 3: CI/CD (R4) + Pre-commit (R5) — can run in parallel
```

**Rationale**:
- Tests must exist BEFORE linting/formatting (so we can validate changes don't break anything)
- R2 and R3 are independent (linting vs type checking)
- R4 and R5 both depend on R1-R3 being in place

---

## Out of Scope

- **Dependency management** (pip-tools, poetry, uv) — current requirements.txt is sufficient
- **Package publishing** (PyPI) — not needed for MCP server
- **Documentation generation** (Sphinx, MkDocs) — existing docs are manual and good
- **Performance benchmarking** — not critical for MCP server
- **Security scanning** (bandit, safety) — can be added later
- **Deployment automation** — MCP servers run locally, not deployed

---

## File Structure After Implementation

```
autogodot/
├── .github/
│   └── workflows/
│       └── ci.yml                    # NEW: CI pipeline
├── core/
│   ├── __init__.py
│   ├── godot_controller.py           # MODIFIED: add type annotations
│   ├── mcp_server.py                 # MODIFIED: add type annotations
│   └── vision_qa.py                  # MODIFIED: add type annotations
├── tests/                            # NEW: test directory
│   ├── __init__.py
│   ├── conftest.py                   # NEW: shared fixtures
│   ├── test_godot_controller.py      # NEW: controller tests
│   ├── test_vision_qa.py             # NEW: vision tests
│   └── test_mcp_server.py            # NEW: server tests
├── config/
├── docs/
├── scripts/
├── .gitignore
├── .pre-commit-config.yaml           # NEW: pre-commit hooks
├── pyproject.toml                    # NEW: project config (ruff, black, mypy, pytest)
├── requirements.txt                  # MODIFIED: add dev dependencies
└── README.md
```

---

## Success Criteria

1. `pytest` passes with ≥80% coverage on core modules
2. `ruff check` passes with zero errors
3. `black --check` passes with no changes needed
4. `mypy core/` passes with zero errors
5. GitHub Actions workflow runs on PRs and passes
6. Pre-commit hooks block commits with quality issues
7. All existing functionality preserved (manual verification)
