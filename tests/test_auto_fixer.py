"""Tests for the auto fixer module."""

from pathlib import Path
import pytest

from core.auto_fixer import AutoFixer


@pytest.fixture
def fixer(tmp_path: Path) -> AutoFixer:
    """Create an auto fixer instance with a temp project directory."""
    return AutoFixer(project_dir=tmp_path)


class TestAutoFixer:
    """Test AutoFixer."""

    def test_fix_trailing_whitespace(self, fixer: AutoFixer) -> None:
        """Test removing trailing whitespace."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        script_file.write_text("var x = 5   \nvar y = 10  \n", encoding="utf-8")

        result = fixer.fix_errors("scripts/player.gd", [])
        assert result["fixed"] is True
        assert "Removed trailing whitespace" in result["fixes"]
        assert "var x = 5\nvar y = 10\n" == result["new_content"]

    def test_fix_common_typos(self, fixer: AutoFixer) -> None:
        """Test fixing common GDScript typos."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        script_file.write_text("onready var x = 0\n", encoding="utf-8")

        # Manually create a file with typo
        script_file.write_text("onredy var x = 0\n", encoding="utf-8")

        result = fixer.fix_errors("scripts/player.gd", [])
        assert result["fixed"] is True
        assert "onready" in result["new_content"]

    def test_fix_double_spaces(self, fixer: AutoFixer) -> None:
        """Test fixing double spaces."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        script_file.write_text("var  x  =  5\n", encoding="utf-8")

        result = fixer.fix_errors("scripts/player.gd", [])
        assert result["fixed"] is True
        assert "var x = 5\n" == result["new_content"]

    def test_fix_file_not_found(self, fixer: AutoFixer) -> None:
        """Test handling of non-existent file."""
        result = fixer.fix_errors("scripts/missing.gd", [])
        assert result["fixed"] is False
        assert "not found" in result.get("error", "").lower()

    def test_validate_and_fix_valid(self, fixer: AutoFixer) -> None:
        """Test validating a valid file."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        script_file.write_text(
            "extends CharacterBody2D\n\nvar speed = 100\n", encoding="utf-8"
        )

        result = fixer.validate_and_fix("scripts/player.gd")
        assert result["valid"] is True

    def test_validate_and_fix_missing_extends(self, fixer: AutoFixer) -> None:
        """Test validating file with missing extends."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        script_file.write_text("var x = 5\n", encoding="utf-8")

        result = fixer.validate_and_fix("scripts/player.gd")
        assert len(result["issues"]) > 0
        assert any("extends" in issue for issue in result["issues"])

    def test_validate_and_fix_trailing_whitespace(self, fixer: AutoFixer) -> None:
        """Test validating file with trailing whitespace."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        script_file.write_text(
            "extends Node\n\nvar x = 5   \n", encoding="utf-8"
        )

        result = fixer.validate_and_fix("scripts/player.gd")
        assert "trailing whitespace" in str(result["issues"]).lower()
        assert len(result["fixes"]) > 0

    def test_validate_and_fix_file_not_found(self, fixer: AutoFixer) -> None:
        """Test validating non-existent file."""
        result = fixer.validate_and_fix("scripts/missing.gd")
        assert result["valid"] is False
        assert "not found" in str(result["issues"]).lower()

    def test_fix_preserves_content(self, fixer: AutoFixer) -> None:
        """Test that fixing doesn't destroy valid content."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        # Use spaces for indentation (consistent with our fix behavior)
        original = "extends CharacterBody2D\n\nfunc _ready() -> void:\n    pass\n"
        script_file.write_text(original, encoding="utf-8")

        result = fixer.fix_errors("scripts/player.gd", [])
        # Content should be unchanged (no fixes needed)
        assert result["new_content"] == original

    def test_fix_mixed_indentation(self, fixer: AutoFixer) -> None:
        """Test fixing mixed tabs and spaces."""
        script_dir = fixer.project_dir / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "player.gd"
        # Mix of tabs and spaces
        script_file.write_text(
            "extends Node\n\tvar x = 5\n    var y = 10\n", encoding="utf-8"
        )

        result = fixer.fix_errors("scripts/player.gd", [])
        # Should have fixed indentation (tabs to spaces)
        assert result["fixed"] is True
        assert "\t" not in result["new_content"]
