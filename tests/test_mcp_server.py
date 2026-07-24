"""Tests for MCP server tool registration and validation."""

from __future__ import annotations

import pytest

# Skip all MCP server tests if mcp is not installed
try:
    from mcp.server.fastmcp import FastMCP  # noqa: F401

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

pytestmark = pytest.mark.skipif(not HAS_MCP, reason="mcp package not installed")


class TestToolRegistration:
    """Verify MCP tools are properly registered."""

    def test_write_game_file_exists(self):
        """write_game_file tool is registered."""
        from core.mcp_server import write_game_file

        assert callable(write_game_file)

    def test_run_godot_test_exists(self):
        """run_godot_test tool is registered."""
        from core.mcp_server import run_godot_test

        assert callable(run_godot_test)

    def test_capture_game_screen_exists(self):
        """capture_game_screen tool is registered."""
        from core.mcp_server import capture_game_screen

        assert callable(capture_game_screen)


class TestWriteGameFile:
    """Tests for write_game_file tool."""

    async def test_write_game_file_success(self, tmp_godot_project, monkeypatch):
        """File is written successfully."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import write_game_file

        result = await write_game_file(
            file_path="scripts/test.gd",
            content="extends Node\nfunc _ready():\n    print('Hello')",
        )

        assert "OK" in result
        assert (tmp_godot_project / "scripts" / "test.gd").exists()

    async def test_write_game_file_creates_dirs(self, tmp_godot_project, monkeypatch):
        """Intermediate directories are created when create_dirs=True."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import write_game_file

        result = await write_game_file(
            file_path="deep/nested/path/test.gd",
            content="extends Node",
            create_dirs=True,
        )

        assert "OK" in result
        assert (tmp_godot_project / "deep" / "nested" / "path" / "test.gd").exists()

    async def test_path_traversal_protection(self, tmp_godot_project, monkeypatch):
        """Path traversal is blocked."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import write_game_file

        result = await write_game_file(
            file_path="../../etc/passwd",
            content="malicious content",
        )

        assert "ERROR" in result
        assert "traversal" in result.lower()

    async def test_write_game_file_overwrites(self, tmp_godot_project, monkeypatch):
        """Existing file is overwritten."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create initial file
        test_file = tmp_godot_project / "scripts" / "test.gd"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("original content")

        from core.mcp_server import write_game_file

        result = await write_game_file(
            file_path="scripts/test.gd",
            content="new content",
        )

        assert "OK" in result
        assert test_file.read_text() == "new content"


class TestGdInit:
    """Tests for gdinit tool."""

    async def test_gdinit_creates_project_2d(self, tmp_godot_project, monkeypatch):
        """gdinit creates a complete 2D project structure."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.scene",
            __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(
                tmp_godot_project
            ),
        )

        import json

        from core.mcp_server import gdinit

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
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.scene",
            __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(
                tmp_godot_project
            ),
        )

        import json

        from core.mcp_server import gdinit

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
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import gdinit

        result = await gdinit(project_name="test", project_type="invalid")
        assert "ERROR" in result

    async def test_gdinit_invalid_project_name(self, tmp_godot_project, monkeypatch):
        """gdinit rejects invalid project name."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import gdinit

        result = await gdinit(project_name="my game!", project_type="2d")
        assert "ERROR" in result

    async def test_gdinit_creates_folders(self, tmp_godot_project, monkeypatch):
        """gdinit creates all required folders."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.scene",
            __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(
                tmp_godot_project
            ),
        )

        from core.mcp_server import gdinit

        await gdinit(project_name="test", project_type="2d")

        assert (tmp_godot_project / "scenes").is_dir()
        assert (tmp_godot_project / "scripts").is_dir()
        assert (tmp_godot_project / "assets" / "sprites").is_dir()
        assert (tmp_godot_project / "assets" / "audio").is_dir()
        assert (tmp_godot_project / "assets" / "themes").is_dir()


class TestGdExplore:
    """Tests for gdexplore tool."""

    async def test_gdexplore_empty_project(self, tmp_godot_project, monkeypatch):
        """gdexplore analyzes empty project."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import gdexplore
        import json

        result = await gdexplore()
        data = json.loads(result)

        assert "features_found" in data
        assert "features_missing" in data
        assert "suggestions" in data
        assert data["total_scenes"] == 0
        assert data["total_scripts"] == 0

    async def test_gdexplore_with_player(self, tmp_godot_project, monkeypatch):
        """gdexplore detects player scene."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create a player scene
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scenes" / "player.tscn").write_text(
            '[gd_scene load_steps=2]\n[node name="Player" type="CharacterBody2D"]'
        )

        from core.mcp_server import gdexplore
        import json

        result = await gdexplore()
        data = json.loads(result)

        assert "player_scene" in data["features_found"]

    async def test_gdexplore_with_signals(self, tmp_godot_project, monkeypatch):
        """gdexplore detects signal system."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create a script with signals
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\nsignal health_changed\nfunc _ready():\n\thealth_changed.emit()"
        )

        from core.mcp_server import gdexplore
        import json

        result = await gdexplore()
        data = json.loads(result)

        assert "signal_system" in data["features_found"]


class TestGdOptimize:
    """Tests for gdoptimize tool."""

    async def test_gdoptimize_finds_untyped_vars(self, tmp_godot_project, monkeypatch):
        """gdoptimize finds untyped variables."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create script with untyped var
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\nvar health = 100\nvar speed = 200.0"
        )

        from core.mcp_server import gdoptimize
        import json

        result = await gdoptimize()
        data = json.loads(result)

        assert data["total_findings"] > 0
        assert any(f["issue"] == "Untyped variable" for f in data["findings"])

    async def test_gdoptimize_finds_missing_collision(self, tmp_godot_project, monkeypatch):
        """gdoptimize finds physics body without collision."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create scene with CharacterBody2D but no CollisionShape
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scenes" / "player.tscn").write_text(
            '[gd_scene]\n[node name="Player" type="CharacterBody2D"]'
        )

        from core.mcp_server import gdoptimize
        import json

        result = await gdoptimize()
        data = json.loads(result)

        assert any(
            f["issue"] == "Physics body without collision shape" for f in data["findings"]
        )

    async def test_gdoptimize_empty_project(self, tmp_godot_project, monkeypatch):
        """gdoptimize handles empty project."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import gdoptimize
        import json

        result = await gdoptimize()
        data = json.loads(result)

        assert "findings" in data
        assert isinstance(data["findings"], list)


class TestGdValidate:
    """Tests for gdvalidate tool."""

    async def test_gdvalidate_empty_project(self, tmp_godot_project, monkeypatch):
        """gdvalidate reports missing structure."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import gdvalidate
        import json

        result = await gdvalidate()
        data = json.loads(result)

        assert "score" in data
        assert "passed" in data
        assert "warnings" in data
        assert "errors" in data
        # Should have errors for missing folders and project.godot
        assert len(data["errors"]) > 0

    async def test_gdvalidate_good_project(self, tmp_godot_project, monkeypatch):
        """gdvalidate scores well-structured project."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create proper structure
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "project.godot").write_text("config_version=5")
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\nvar health: int = 100"
        )

        from core.mcp_server import gdvalidate
        import json

        result = await gdvalidate()
        data = json.loads(result)

        assert data["score"] > 50
        assert any("project.godot exists" in p for p in data["passed"])

    async def test_gdvalidate_naming_check(self, tmp_godot_project, monkeypatch):
        """gdvalidate checks naming conventions."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create script with bad name
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "My Script.gd").write_text("extends Node")

        from core.mcp_server import gdvalidate
        import json

        result = await gdvalidate()
        data = json.loads(result)

        assert any("not snake_case" in w for w in data["warnings"])
