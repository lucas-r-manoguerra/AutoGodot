"""Shared fixtures for AutoGodot MCP tool tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_godot_project(tmp_path: Path) -> Path:
    """Create a temporary Godot project directory."""
    project_dir = tmp_path / "godot_project"
    project_dir.mkdir()
    (project_dir / "project.godot").write_text('[gd_resource type="ProjectSettings"]\n')
    return project_dir
