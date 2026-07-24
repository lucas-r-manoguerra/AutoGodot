# AutoGodot Infrastructure Design

## Overview

Implement a production-grade infrastructure for AutoGodot using pytest for testing, ruff for linting, black for formatting, mypy for type checking, GitHub Actions for CI/CD, and pre-commit for local quality gates. All configuration centralized in pyproject.toml. Tests use comprehensive mocks to avoid requiring Godot or screen hardware.

---

## Architecture Decisions

### AD1: Testing Framework — pytest + pytest-asyncio
- **Decision**: pytest with pytest-asyncio for async test support
- **Rationale**: pytest is the Python standard; pytest-asyncio handles async tool functions naturally. pytest-cov for coverage reporting.
- **Alternatives considered**: unittest (verbose, no async support), tox (overkill for this project size)

### AD2: Linting Tool — ruff
- **Decision**: ruff for linting and import sorting
- **Rationale**: 10-100x faster than flake8, replaces flake8+isort+pyflakes+pycodestyle in one tool. Active development, excellent Pydantic support.
- **Alternatives considered**: flake8 (slower, needs plugins), pylint (too strict for this project)

### AD3: Formatting Tool — black
- **Decision**: black for code formatting
- **Rationale**: Opinionated, zero config, battle-tested. ruff can also format but black is more mature.
- **Alternatives considered**: ruff format (newer, less proven), autopep8 (too permissive)

### AD4: Type Checker — mypy
- **Decision**: mypy with gradual strictness
- **Rationale**: Best Pydantic integration, gradual adoption possible, GitHub Actions support.
- **Alternatives considered**: pyright (faster but less Pydantic support), pytype (Google-specific)

### AD5: CI/CD — GitHub Actions
- **Decision**: GitHub Actions with parallel jobs
- **Rationale**: Free for open source, native GitHub integration, YAML-based.
- **Alternatives considered**: GitLab CI (not using GitLab), CircleCI (overkill)

### AD6: Pre-commit — pre-commit framework
- **Decision**: pre-commit with ruff, black, mypy hooks
- **Rationale**: Standard Python pre-commit framework, easy to configure, auto-updates.
- **Alternatives considered**: husky (Node.js), lefthook (Go-based)

---

## Detailed Design

### 1. Testing Architecture

#### File Structure
```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_godot_controller.py       # GodotController tests
├── test_vision_qa.py              # VisionQA tests
└── test_mcp_server.py             # MCP server tool tests
```

#### Mock Strategy

**GodotController** — Mock `asyncio.create_subprocess_exec`:
```python
# conftest.py
@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock asyncio.create_subprocess_exec for GodotController tests."""
    async def mock_create(*args, **kwargs):
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"stdout", b"stderr")
        mock_proc.returncode = 0
        mock_proc.pid = 12345
        return mock_proc
    monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create)
```

**VisionQA** — Mock `mss.mss()` and `PIL.Image`:
```python
# conftest.py
@pytest.fixture
def mock_screen_capture(monkeypatch):
    """Mock mss and PIL for VisionQA tests."""
    mock_mss = MagicMock()
    mock_mss.__enter__.return_value.monitors = [
        {"top": 0, "left": 0, "width": 1920, "height": 1080}
    ]
    mock_mss.__enter__.return_value.grab.return_value = MagicMock(
        rgb=b"\x00" * (1920 * 1080 * 3),
        size=(1920, 1080)
    )
    monkeypatch.setattr("mss.mss", lambda: mock_mss.__enter__())
```

**MCP Server** — Test tool registration and input validation:
```python
# test_mcp_server.py
def test_write_game_file_registration():
    """Verify write_game_file tool is registered."""
    # Import and check tool registry

def test_path_traversal_protection():
    """Verify path traversal is blocked."""
    # Call with "../../etc/passwd" and verify ERROR response
```

#### Fixtures Design (conftest.py)

```python
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def tmp_godot_project(tmp_path):
    """Create a temporary Godot project directory."""
    project_dir = tmp_path / "godot_project"
    project_dir.mkdir()
    (project_dir / "project.godot").write_text("[gd_resource type=\"ProjectSettings\"]")
    return project_dir

@pytest.fixture
def godot_controller(tmp_godot_project):
    """Create a GodotController with temp project."""
    from core.godot_controller import GodotController
    return GodotController(godot_path="godot4", project_dir=tmp_godot_project)

@pytest.fixture
def vision_qa():
    """Create a VisionQA instance."""
    from core.vision_qa import VisionQA
    return VisionQA()

@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess for GodotController tests."""
    # ... as above

@pytest.fixture
def mock_screen_capture(monkeypatch):
    """Mock screen capture for VisionQA tests."""
    # ... as above
```

#### Coverage Configuration

- Target: ≥80% for `core/*.py`
- Excluded: `__init__.py`, `if __name__ == "__main__"` blocks
- Reports: terminal + XML (for CI)

---

### 2. Tool Configuration (pyproject.toml)

```toml
[project]
name = "autogodot"
version = "0.1.0"
description = "Autonomous game development framework for Godot 4.x via MCP"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "mss>=9.0.0",
    "Pillow>=10.0.0",
    "python-xlib>=0.33",
    "aiofiles>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.4.0",
    "black>=24.0.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]

# --- Ruff Configuration ---
[tool.ruff]
target-version = "py310"
line-length = 88

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by black)
]

[tool.ruff.lint.isort]
known-first-party = ["core"]

# --- Black Configuration ---
[tool.black]
target-version = ["py310"]
line-length = 88

# --- Mypy Configuration ---
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Gradual: start permissive
check_untyped_defs = true

[[tool.mypy.overrides]]
module = ["mss", "mss.tools", "PIL", "python_xlib.*"]
ignore_missing_imports = true

# --- Pytest Configuration ---
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]

[tool.coverage.run]
source = ["core"]
omit = ["tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
fail_under = 80
```

---

### 3. CI/CD Pipeline (GitHub Actions)

#### .github/workflows/ci.yml

```yaml
name: CI

on:
  pull_request:
    branches: [main, master]
  push:
    branches: [main, master]

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: pip install ruff
      - name: Run ruff
        run: ruff check core/ tests/

  format:
    name: Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: pip install black
      - name: Check formatting
        run: black --check core/ tests/

  typecheck:
    name: Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: |
          pip install mypy
          pip install -r requirements.txt
      - name: Run mypy
        run: mypy core/

  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest --cov=core --cov-report=term-missing --cov-report=xml
      - name: Upload coverage
        if: matrix.python-version == '3.10'
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
```

---

### 4. Pre-commit Configuration

#### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0.0]
        args: [--ignore-missing-imports]
```

---

### 5. File Changes Manifest

| Action | File | Description |
|--------|------|-------------|
| CREATE | `pyproject.toml` | Project config: ruff, black, mypy, pytest, coverage |
| CREATE | `tests/__init__.py` | Test package marker |
| CREATE | `tests/conftest.py` | Shared fixtures (mocks, temp projects) |
| CREATE | `tests/test_godot_controller.py` | Controller tests (subprocess mocking) |
| CREATE | `tests/test_vision_qa.py` | Vision tests (screen capture mocking) |
| CREATE | `tests/test_mcp_server.py` | Server tests (tool registration, validation) |
| CREATE | `.github/workflows/ci.yml` | GitHub Actions CI pipeline |
| CREATE | `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| MODIFY | `requirements.txt` | Add dev dependencies section comment |
| MODIFY | `core/godot_controller.py` | Add type annotations |
| MODIFY | `core/mcp_server.py` | Add type annotations |
| MODIFY | `core/vision_qa.py` | Add type annotations |

---

## Implementation Order

```
Step 1: Create pyproject.toml with all tool configurations
Step 2: Create tests/ directory with conftest.py and fixtures
Step 3: Create test_godot_controller.py (mock subprocess)
Step 4: Create test_vision_qa.py (mock screen capture)
Step 5: Create test_mcp_server.py (tool registration, validation)
Step 6: Add type annotations to core/*.py files
Step 7: Create .github/workflows/ci.yml
Step 8: Create .pre-commit-config.yaml
Step 9: Update requirements.txt with dev dependencies
Step 10: Run full validation (pytest + ruff + black + mypy)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Tests break existing functionality | Run tests BEFORE and AFTER changes |
| Type annotations break runtime | Add gradually, start with permissive mypy config |
| CI/CD too slow | Parallel jobs, cache pip dependencies |
| Pre-commit too strict | Use --no-verify for emergency commits |
| Coverage target too high | Start at 80%, adjust based on实际情况 |
