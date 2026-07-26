"""Tests for MCP server tool registration."""

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
        from core.tools.file_ops import write_game_file

        assert callable(write_game_file)

    def test_run_godot_test_exists(self):
        """run_godot_test tool is registered."""
        from core.tools.execution import run_godot_test

        assert callable(run_godot_test)

    def test_capture_game_screen_exists(self):
        """capture_game_screen tool is registered."""
        from core.tools.visual_qa import capture_game_screen

        assert callable(capture_game_screen)

    def test_read_scene_exists(self):
        """read_scene tool is registered."""
        from core.tools.scene_ops import read_scene

        assert callable(read_scene)

    def test_create_scene_exists(self):
        """create_scene tool is registered."""
        from core.tools.scene_ops import create_scene

        assert callable(create_scene)

    def test_modify_scene_exists(self):
        """modify_scene tool is registered."""
        from core.tools.scene_ops import modify_scene

        assert callable(modify_scene)

    def test_read_script_exists(self):
        """read_script tool is registered."""
        from core.tools.script_ops import read_script

        assert callable(read_script)

    def test_create_script_exists(self):
        """create_script tool is registered."""
        from core.tools.script_ops import create_script

        assert callable(create_script)

    def test_modify_script_exists(self):
        """modify_script tool is registered."""
        from core.tools.script_ops import modify_script

        assert callable(modify_script)

    def test_gdinit_exists(self):
        """gdinit tool is registered."""
        from core.tools.project_scaffold import gdinit

        assert callable(gdinit)

    def test_gdexplore_exists(self):
        """gdexplore tool is registered."""
        from core.tools.analysis import gdexplore

        assert callable(gdexplore)

    def test_gdoptimize_exists(self):
        """gdoptimize tool is registered."""
        from core.tools.analysis import gdoptimize

        assert callable(gdoptimize)

    def test_gdvalidate_exists(self):
        """gdvalidate tool is registered."""
        from core.tools.analysis import gdvalidate

        assert callable(gdvalidate)

    def test_gdcheck_exists(self):
        """gdcheck tool is registered."""
        from core.tools.analysis import gdcheck

        assert callable(gdcheck)

    def test_godot_errors_exists(self):
        """godot_errors tool is registered."""
        from core.tools.error_handling import godot_errors

        assert callable(godot_errors)

    def test_auto_fix_exists(self):
        """auto_fix tool is registered."""
        from core.tools.error_handling import auto_fix

        assert callable(auto_fix)

    def test_run_tests_exists(self):
        """run_tests tool is registered."""
        from core.tools.execution import run_tests

        assert callable(run_tests)

    def test_godot_gotchas_exists(self):
        """godot_gotchas tool is registered."""
        from core.tools.knowledge import godot_gotchas

        assert callable(godot_gotchas)
