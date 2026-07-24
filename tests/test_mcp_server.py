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
        monkeypatch.setattr("core.mcp_server.scene", 
                          __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(tmp_godot_project))

        from core.mcp_server import gdinit
        import json

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
        monkeypatch.setattr("core.mcp_server.scene", 
                          __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(tmp_godot_project))

        from core.mcp_server import gdinit
        import json

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
        monkeypatch.setattr("core.mcp_server.scene", 
                          __import__("core.scene_builder", fromlist=["SceneBuilder"]).SceneBuilder(tmp_godot_project))

        from core.mcp_server import gdinit

        await gdinit(project_name="test", project_type="2d")

        assert (tmp_godot_project / "scenes").is_dir()
        assert (tmp_godot_project / "scripts").is_dir()
        assert (tmp_godot_project / "assets" / "sprites").is_dir()
        assert (tmp_godot_project / "assets" / "audio").is_dir()
        assert (tmp_godot_project / "assets" / "themes").is_dir()
