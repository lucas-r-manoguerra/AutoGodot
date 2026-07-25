"""Tests for GDScript syntax validator."""

from __future__ import annotations

import pytest

from core.gd_parser import GDScriptValidator


class TestGDScriptValidator:
    """Tests for GDScriptValidator class."""

    def test_validate_valid_script(self, tmp_godot_project):
        """Valid script passes validation."""
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\n\nvar health: int = 100\n\nfunc _ready() -> void:\n\tpass"
        )

        validator = GDScriptValidator(project_dir=tmp_godot_project)
        result = validator.validate_file("scripts/player.gd")

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_invalid_script(self, tmp_godot_project):
        """Invalid script fails validation."""
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "bad.gd").write_text(
            "extends Node\n\nfunc _ready()\n\tpass"
        )

        validator = GDScriptValidator(project_dir=tmp_godot_project)
        result = validator.validate_file("scripts/bad.gd")

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_missing_file(self, tmp_godot_project):
        """Missing file returns error."""
        validator = GDScriptValidator(project_dir=tmp_godot_project)
        result = validator.validate_file("scripts/missing.gd")

        assert result["valid"] is False
        assert "not found" in result["errors"][0]["message"].lower()

    def test_validate_non_gd_file(self, tmp_godot_project):
        """Non-.gd files are skipped."""
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scenes" / "main.tscn").write_text("[gd_scene]")

        validator = GDScriptValidator(project_dir=tmp_godot_project)
        result = validator.validate_file("scenes/main.tscn")

        assert result["valid"] is True

    def test_validate_content(self, tmp_godot_project):
        """validate_content checks string content."""
        validator = GDScriptValidator(project_dir=tmp_godot_project)

        # Valid content
        result = validator.validate_content("extends Node\n\nfunc _ready() -> void:\n\tpass")
        assert result["valid"] is True

        # Invalid content
        result = validator.validate_content("extends Node\n\nfunc _ready()\n\tpass")
        assert result["valid"] is False

    def test_validate_project(self, tmp_godot_project):
        """validate_project scans all .gd files."""
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "good.gd").write_text(
            "extends Node\n\nfunc _ready() -> void:\n\tpass"
        )
        (tmp_godot_project / "scripts" / "bad.gd").write_text(
            "extends Node\n\nfunc _ready()\n\tpass"
        )

        validator = GDScriptValidator(project_dir=tmp_godot_project)
        result = validator.validate_project()

        assert result["total_files"] == 2
        assert result["valid_files"] == 1
        assert result["invalid_files"] == 1

    def test_path_traversal_protection(self, tmp_godot_project):
        """Path traversal is blocked."""
        validator = GDScriptValidator(project_dir=tmp_godot_project)
        result = validator.validate_file("../../../etc/passwd")

        assert result["valid"] is False
        assert "traversal" in result["errors"][0]["message"].lower()
