"""Tests for gdexplore, gdoptimize, gdvalidate, gdcheck tools."""

from __future__ import annotations

import json

import pytest


class TestGdExplore:
    """Tests for gdexplore tool."""

    async def test_gdexplore_empty_project(self, tmp_godot_project, monkeypatch):
        """gdexplore analyzes empty project."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        from core.tools.analysis import gdexplore

        result = await gdexplore()
        data = json.loads(result)

        assert "features_found" in data
        assert "features_missing" in data
        assert "suggestions" in data
        assert data["total_scenes"] == 0
        assert data["total_scripts"] == 0

    async def test_gdexplore_with_player(self, tmp_godot_project, monkeypatch):
        """gdexplore detects player scene."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        # Create a player scene
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scenes" / "player.tscn").write_text(
            '[gd_scene load_steps=2]\n[node name="Player" type="CharacterBody2D"]'
        )

        from core.tools.analysis import gdexplore

        result = await gdexplore()
        data = json.loads(result)

        assert "player_scene" in data["features_found"]

    async def test_gdexplore_with_signals(self, tmp_godot_project, monkeypatch):
        """gdexplore detects signal system."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        # Create a script with signals
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\nsignal health_changed\nfunc _ready():\n\thealth_changed.emit()"
        )

        from core.tools.analysis import gdexplore

        result = await gdexplore()
        data = json.loads(result)

        assert "signal_system" in data["features_found"]


class TestGdOptimize:
    """Tests for gdoptimize tool."""

    async def test_gdoptimize_finds_untyped_vars(self, tmp_godot_project, monkeypatch):
        """gdoptimize finds untyped variables."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        # Create script with untyped var
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\nvar health = 100\nvar speed = 200.0"
        )

        from core.tools.analysis import gdoptimize

        result = await gdoptimize()
        data = json.loads(result)

        assert data["total_findings"] > 0
        assert any(f["issue"] == "Untyped variable" for f in data["findings"])

    async def test_gdoptimize_finds_missing_collision(
        self, tmp_godot_project, monkeypatch
    ):
        """gdoptimize finds physics body without collision."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        # Create scene with CharacterBody2D but no CollisionShape
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scenes" / "player.tscn").write_text(
            '[gd_scene]\n[node name="Player" type="CharacterBody2D"]'
        )

        from core.tools.analysis import gdoptimize

        result = await gdoptimize()
        data = json.loads(result)

        assert any(
            f["issue"] == "Physics body without collision shape"
            for f in data["findings"]
        )

    async def test_gdoptimize_empty_project(self, tmp_godot_project, monkeypatch):
        """gdoptimize handles empty project."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        from core.tools.analysis import gdoptimize

        result = await gdoptimize()
        data = json.loads(result)

        assert "findings" in data
        assert isinstance(data["findings"], list)


class TestGdValidate:
    """Tests for gdvalidate tool."""

    async def test_gdvalidate_empty_project(self, tmp_godot_project, monkeypatch):
        """gdvalidate reports missing structure."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        from core.tools.analysis import gdvalidate

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
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        # Create proper structure
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "project.godot").write_text("config_version=5")
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\nvar health: int = 100"
        )

        from core.tools.analysis import gdvalidate

        result = await gdvalidate()
        data = json.loads(result)

        assert data["score"] > 50
        assert any("project.godot exists" in p for p in data["passed"])

    async def test_gdvalidate_naming_check(self, tmp_godot_project, monkeypatch):
        """gdvalidate checks naming conventions."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)

        # Create script with bad name
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "My Script.gd").write_text("extends Node")

        from core.tools.analysis import gdvalidate

        result = await gdvalidate()
        data = json.loads(result)

        assert any("not snake_case" in w for w in data["warnings"])


class TestGdCheck:
    """Tests for gdcheck tool."""

    async def test_gdcheck_valid_file(self, tmp_godot_project, monkeypatch):
        """gdcheck validates a valid .gd file."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        # Create valid script
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\n\nvar health: int = 100\n\nfunc _ready() -> void:\n\tpass"
        )

        from core.tools.analysis import gdcheck

        result = await gdcheck(file_path="scripts/player.gd")
        data = json.loads(result)

        assert data["valid"] is True
        assert len(data["errors"]) == 0

    async def test_gdcheck_invalid_file(self, tmp_godot_project, monkeypatch):
        """gdcheck detects syntax errors."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        # Create invalid script (missing colon after func)
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "bad.gd").write_text(
            "extends Node\n\nfunc _ready()\n\tpass"
        )

        from core.tools.analysis import gdcheck

        result = await gdcheck(file_path="scripts/bad.gd")
        data = json.loads(result)

        assert data["valid"] is False
        assert len(data["errors"]) > 0

    async def test_gdcheck_all_files(self, tmp_godot_project, monkeypatch):
        """gdcheck validates all .gd files when no path given."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        # Create multiple scripts
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\n\nvar health: int = 100"
        )
        (tmp_godot_project / "scripts" / "enemy.gd").write_text(
            "extends CharacterBody2D\n\nvar damage: int = 10"
        )

        from core.tools.analysis import gdcheck

        result = await gdcheck(file_path="")
        data = json.loads(result)

        assert data["total_files"] == 2
        assert data["valid_files"] == 2
        assert data["invalid_files"] == 0

    async def test_gdcheck_nonexistent_file(self, tmp_godot_project, monkeypatch):
        """gdcheck handles missing files."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.analysis import gdcheck

        result = await gdcheck(file_path="scripts/missing.gd")
        data = json.loads(result)

        assert data["valid"] is False
        assert "not found" in data["errors"][0]["message"].lower()


class TestGdcheckSemantic:
    """Tests for gdcheck semantic analysis features."""

    async def test_mixed_indentation_detected(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck detects mixed tabs and spaces."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.analysis import gdcheck

        # Write file with mixed indentation
        bad_script = "extends Node\n\nfunc _ready():\n\tpass\n    var x = 1"
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "mixed.gd").write_text(bad_script)

        result = await gdcheck(file_path="scripts/mixed.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "indentation" for i in issues)

    async def test_missing_extends_detected(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck warns about missing extends/class_name."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.analysis import gdcheck

        # Script without extends or class_name
        bare_script = "var x = 1\n\nfunc _ready():\n    pass"
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "bare.gd").write_text(bare_script)

        result = await gdcheck(file_path="scripts/bare.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "structure" for i in issues)

    async def test_large_file_warning(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck warns about files over 300 lines."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.analysis import gdcheck

        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "big.gd").write_text(
            "extends Node\n\n" + "\n".join(f"# line {i}" for i in range(350))
        )

        result = await gdcheck(file_path="scripts/big.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "maintainability" for i in issues)

    async def test_class_name_cli_warning(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck warns about class_name usage for CLI compatibility."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.analysis import gdcheck

        script_with_class = "class_name MyData\nextends RefCounted\n"
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "mydata.gd").write_text(script_with_class)

        result = await gdcheck(file_path="scripts/mydata.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "cli_compatibility" for i in issues)

    async def test_godot3_api_misuse_detected(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck detects Godot 3 API patterns."""
        monkeypatch.setattr("core.tools.analysis.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.tools.analysis.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.tools.analysis import gdcheck

        old_api = (
            "extends CharacterBody2D\n\n"
            "export var speed = 100\n"
            "onready var sprite = $Sprite\n\n"
            "func _ready():\n"
            "    move_and_slide(Vector2(1,0) * speed)\n"
            "    connect('hit', self, '_on_hit')\n"
        )
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "old_api.gd").write_text(old_api)

        result = await gdcheck(file_path="scripts/old_api.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        api_issues = [i for i in issues if i["type"] == "api_misuse"]
        # Should detect at least: export var, onready var, move_and_slide(args), string connect
        assert len(api_issues) >= 3
