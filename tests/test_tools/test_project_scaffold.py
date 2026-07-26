"""Tests for gdinit tool."""

from __future__ import annotations

import json

import pytest


class TestGdInit:
    """Tests for gdinit tool."""

    async def test_gdinit_creates_project_2d(self, tmp_godot_project, monkeypatch):
        """gdinit creates a complete 2D project structure."""
        monkeypatch.setattr("core.tools.project_scaffold.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.project_scaffold.scene",
            __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(
                tmp_godot_project
            ),
        )

        from core.tools.project_scaffold import gdinit

        result = await gdinit(project_name="test_game", project_type="2d")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["project_name"] == "test_game"
        assert data["project_type"] == "2d"
        assert "project.godot" in data["files_created"]
        assert "scenes/player.tscn" in data["files_created"]
        assert "scenes/main.tscn" in data["files_created"]
        assert "scripts/player.gd" in data["files_created"]
        assert "scripts/game_manager.gd" in data["files_created"]
        assert (tmp_godot_project / "project.godot").exists()
        assert (tmp_godot_project / "scenes" / "player.tscn").exists()

    async def test_gdinit_creates_project_3d(self, tmp_godot_project, monkeypatch):
        """gdinit creates a complete 3D project structure."""
        monkeypatch.setattr("core.tools.project_scaffold.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.project_scaffold.scene",
            __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(
                tmp_godot_project
            ),
        )

        from core.tools.project_scaffold import gdinit

        result = await gdinit(project_name="test_game_3d", project_type="3d")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["project_type"] == "3d"
        assert (tmp_godot_project / "project.godot").exists()
        # 3D project should use forward_plus renderer
        content = (tmp_godot_project / "project.godot").read_text()
        assert "forward_plus" in content

    async def test_gdinit_invalid_project_type(self, tmp_godot_project, monkeypatch):
        """gdinit rejects invalid project type."""
        monkeypatch.setattr("core.tools.project_scaffold.GODOT_PROJECT", tmp_godot_project)

        from core.tools.project_scaffold import gdinit

        result = await gdinit(project_name="test", project_type="invalid")
        assert "ERROR" in result

    async def test_gdinit_invalid_project_name(self, tmp_godot_project, monkeypatch):
        """gdinit rejects invalid project name."""
        monkeypatch.setattr("core.tools.project_scaffold.GODOT_PROJECT", tmp_godot_project)

        from core.tools.project_scaffold import gdinit

        result = await gdinit(project_name="my game!", project_type="2d")
        assert "ERROR" in result

    async def test_gdinit_creates_folders(self, tmp_godot_project, monkeypatch):
        """gdinit creates all required folders."""
        monkeypatch.setattr("core.tools.project_scaffold.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.project_scaffold.scene",
            __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(
                tmp_godot_project
            ),
        )

        from core.tools.project_scaffold import gdinit

        await gdinit(project_name="test", project_type="2d")

        assert (tmp_godot_project / "scenes").is_dir()
        assert (tmp_godot_project / "scripts").is_dir()
        assert (tmp_godot_project / "assets" / "sprites").is_dir()
        assert (tmp_godot_project / "assets" / "audio").is_dir()
        assert (tmp_godot_project / "assets" / "themes").is_dir()
