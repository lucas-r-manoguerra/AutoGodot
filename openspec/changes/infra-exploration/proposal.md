# AutoGodot Infrastructure Exploration

## Executive Summary

AutoGodot is a Python MCP server (531 lines across 3 core modules) that enables AI agents to develop Godot 4.x games. The project has **excellent documentation** and a **solid setup script**, but is **completely missing testing, CI/CD, linting, and code quality infrastructure**.

## Current State

| Area | Status | Details |
|------|--------|---------|
| **Core Code** | ✅ Solid | 3 modules: mcp_server.py (306L), godot_controller.py (116L), vision_qa.py (109L) |
| **Documentation** | ✅ Excellent | 8 detailed docs covering architecture, setup, MCP tools, Godot communication, visual QA |
| **Setup Script** | ✅ Good | Comprehensive setup_and_run.sh with error handling, color output, multi-path detection |
| **Configuration** | ⚠️ Minimal | Only requirements.txt + .gitignore; no pyproject.toml, no linting config |
| **Testing** | ❌ Missing | Zero test files, no test framework, no test configuration |
| **CI/CD** | ❌ Missing | No GitHub Actions, no GitLab CI, no automated quality gates |
| **Code Quality** | ❌ Missing | No linting (ruff/flake8), no formatting (black/pre-commit), no type checking (mypy) |
| **Packaging** | ❌ Missing | No pyproject.toml, no setup.py, no versioning system |

## Infrastructure Gaps

### 1. Testing (Critical)
- **Zero tests** — no pytest, unittest, or any test framework
- No test directory structure
- No fixtures or mocks
- Risk: MCP server bugs could silently corrupt game files or crash Godot processes

### 2. CI/CD (High)
- No automated testing pipeline
- No quality gates before merge
- No deployment automation

### 3. Code Quality Tools (Medium)
- No linting configuration (ruff recommended for speed)
- No formatting enforcement (black + isort)
- No pre-commit hooks
- Inconsistent string formatting (%-formatting vs f-strings)

### 4. Type Checking (Medium)
- Pydantic models are typed
- Minimal type annotations elsewhere
- No mypy or pyright configuration

### 5. Packaging (Low)
- No pyproject.toml for modern Python packaging
- No version management
- No distribution setup

## Strengths to Preserve

1. **Documentation Quality** — docs/ is comprehensive and well-structured
2. **Setup Script** — setup_and_run.sh is production-ready with multi-path detection
3. **.gitignore** — covers Python, venv, IDE, OS, Godot, env files
4. **Code Structure** — clean separation of concerns (server, controller, vision)

## Recommended Infrastructure Changes

### Phase 1: Testing Foundation
1. Add pytest + pytest-asyncio to requirements.txt
2. Create tests/ directory with:
   - test_godot_controller.py (mock subprocess)
   - test_vision_qa.py (mock mss/Pillow)
   - test_mcp_server.py (test tool registration and validation)
3. Add conftest.py with shared fixtures

### Phase 2: Code Quality
1. Add ruff for linting (fast, replaces flake8+isort+more)
2. Add black for formatting
3. Add pre-commit hooks for automated checks
4. Configure mypy for type checking

### Phase 3: CI/CD
1. GitHub Actions workflow:
   - Lint on PR
   - Run tests on PR
   - Type check on PR
2. Optional: scheduled dependency updates with Dependabot

### Phase 4: Packaging
1. Create pyproject.toml with project metadata
2. Add version management (bump2version or similar)
3. Optional: publish to PyPI if needed

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Untested code could corrupt game files | Critical | Phase 1 testing foundation |
| No CI means bugs merge silently | High | Phase 3 CI/CD |
| Inconsistent code style | Medium | Phase 2 linting/formatting |
| Missing type safety | Medium | Phase 2 mypy |

## Next Steps

1. User decides which infrastructure areas to prioritize
2. Create SDD proposal for chosen area
3. Follow SDD workflow: spec → design → tasks → apply → verify
