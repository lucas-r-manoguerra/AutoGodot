"""Tests for write_game_file tool."""

from __future__ import annotations

import pytest


class TestWriteGameFile:
    """Tests for write_game_file tool."""

    async def test_write_game_file_success(self, tmp_godot_project, monkeypatch):
        """File is written successfully."""
        monkeypatch.setattr("core.tools.file_ops.GODOT_PROJECT", tmp_godot_project)

        from core.tools.file_ops import write_game_file

        result = await write_game_file(
            file_path="scripts/test.gd",
            content="extends Node\nfunc _ready():\n    print('Hello')",
        )

        assert "OK" in result
        assert (tmp_godot_project / "scripts" / "test.gd").exists()

    async def test_write_game_file_creates_dirs(self, tmp_godot_project, monkeypatch):
        """Intermediate directories are created when create_dirs=True."""
        monkeypatch.setattr("core.tools.file_ops.GODOT_PROJECT", tmp_godot_project)

        from core.tools.file_ops import write_game_file

        result = await write_game_file(
            file_path="deep/nested/path/test.gd",
            content="extends Node",
            create_dirs=True,
        )

        assert "OK" in result
        assert (tmp_godot_project / "deep" / "nested" / "path" / "test.gd").exists()

    async def test_path_traversal_protection(self, tmp_godot_project, monkeypatch):
        """Path traversal is blocked."""
        monkeypatch.setattr("core.tools.file_ops.GODOT_PROJECT", tmp_godot_project)

        from core.tools.file_ops import write_game_file

        result = await write_game_file(
            file_path="../../etc/passwd",
            content="malicious content",
        )

        assert "ERROR" in result
        assert "traversal" in result.lower()

    async def test_write_game_file_overwrites(self, tmp_godot_project, monkeypatch):
        """Existing file is overwritten."""
        monkeypatch.setattr("core.tools.file_ops.GODOT_PROJECT", tmp_godot_project)

        # Create initial file
        test_file = tmp_godot_project / "scripts" / "test.gd"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("original content")

        from core.tools.file_ops import write_game_file

        result = await write_game_file(
            file_path="scripts/test.gd",
            content="new content",
        )

        assert "OK" in result
        assert test_file.read_text() == "new content"


class TestWriteGameFileValidation:
    """Tests for write_game_file syntax validation."""

    async def test_write_gd_file_validates_syntax(self, tmp_godot_project, monkeypatch):
        """write_game_file validates .gd files after writing."""
        monkeypatch.setattr("core.tools.file_ops.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.file_ops.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.file_ops import write_game_file

        # Write valid script
        result = await write_game_file(
            file_path="scripts/valid.gd",
            content="extends Node\n\nfunc _ready() -> void:\n\tpass",
        )

        assert "OK:" in result
        assert "SYNTAX ERROR" not in result

    async def test_write_gd_file_reports_syntax_error(
        self, tmp_godot_project, monkeypatch
    ):
        """write_game_file reports syntax errors for invalid .gd files."""
        monkeypatch.setattr("core.tools.file_ops.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.file_ops.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.file_ops import write_game_file

        # Write invalid script (missing colon)
        result = await write_game_file(
            file_path="scripts/bad.gd",
            content="extends Node\n\nfunc _ready()\n\tpass",
        )

        assert "OK:" in result
        assert "SYNTAX ERROR" in result

    async def test_write_non_gd_file_skips_validation(
        self, tmp_godot_project, monkeypatch
    ):
        """write_game_file skips validation for non-.gd files."""
        monkeypatch.setattr("core.tools.file_ops.GODOT_PROJECT", tmp_godot_project)

        from core.tools.file_ops import write_game_file

        result = await write_game_file(
            file_path="scenes/main.tscn",
            content='[gd_scene]\n\n[node name="Main" type="Node"]',
        )

        assert "OK:" in result
        assert "SYNTAX ERROR" not in result
