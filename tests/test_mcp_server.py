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

        import json

        from core.mcp_server import gdexplore

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

        import json

        from core.mcp_server import gdexplore

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

        import json

        from core.mcp_server import gdexplore

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

        import json

        from core.mcp_server import gdoptimize

        result = await gdoptimize()
        data = json.loads(result)

        assert data["total_findings"] > 0
        assert any(f["issue"] == "Untyped variable" for f in data["findings"])

    async def test_gdoptimize_finds_missing_collision(
        self, tmp_godot_project, monkeypatch
    ):
        """gdoptimize finds physics body without collision."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        # Create scene with CharacterBody2D but no CollisionShape
        (tmp_godot_project / "scenes").mkdir()
        (tmp_godot_project / "scenes" / "player.tscn").write_text(
            '[gd_scene]\n[node name="Player" type="CharacterBody2D"]'
        )

        import json

        from core.mcp_server import gdoptimize

        result = await gdoptimize()
        data = json.loads(result)

        assert any(
            f["issue"] == "Physics body without collision shape"
            for f in data["findings"]
        )

    async def test_gdoptimize_empty_project(self, tmp_godot_project, monkeypatch):
        """gdoptimize handles empty project."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        import json

        from core.mcp_server import gdoptimize

        result = await gdoptimize()
        data = json.loads(result)

        assert "findings" in data
        assert isinstance(data["findings"], list)


class TestGdValidate:
    """Tests for gdvalidate tool."""

    async def test_gdvalidate_empty_project(self, tmp_godot_project, monkeypatch):
        """gdvalidate reports missing structure."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        import json

        from core.mcp_server import gdvalidate

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

        import json

        from core.mcp_server import gdvalidate

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

        import json

        from core.mcp_server import gdvalidate

        result = await gdvalidate()
        data = json.loads(result)

        assert any("not snake_case" in w for w in data["warnings"])


class TestGdCheck:
    """Tests for gdcheck tool."""

    async def test_gdcheck_valid_file(self, tmp_godot_project, monkeypatch):
        """gdcheck validates a valid .gd file."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        # Create valid script
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "player.gd").write_text(
            "extends CharacterBody2D\n\nvar health: int = 100\n\nfunc _ready() -> void:\n\tpass"
        )

        import json

        from core.mcp_server import gdcheck

        result = await gdcheck(file_path="scripts/player.gd")
        data = json.loads(result)

        assert data["valid"] is True
        assert len(data["errors"]) == 0

    async def test_gdcheck_invalid_file(self, tmp_godot_project, monkeypatch):
        """gdcheck detects syntax errors."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        # Create invalid script (missing colon after func)
        (tmp_godot_project / "scripts").mkdir()
        (tmp_godot_project / "scripts" / "bad.gd").write_text(
            "extends Node\n\nfunc _ready()\n\tpass"
        )

        import json

        from core.mcp_server import gdcheck

        result = await gdcheck(file_path="scripts/bad.gd")
        data = json.loads(result)

        assert data["valid"] is False
        assert len(data["errors"]) > 0

    async def test_gdcheck_all_files(self, tmp_godot_project, monkeypatch):
        """gdcheck validates all .gd files when no path given."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
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

        import json

        from core.mcp_server import gdcheck

        result = await gdcheck(file_path="")
        data = json.loads(result)

        assert data["total_files"] == 2
        assert data["valid_files"] == 2
        assert data["invalid_files"] == 0

    async def test_gdcheck_nonexistent_file(self, tmp_godot_project, monkeypatch):
        """gdcheck handles missing files."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        import json

        from core.mcp_server import gdcheck

        result = await gdcheck(file_path="scripts/missing.gd")
        data = json.loads(result)

        assert data["valid"] is False
        assert "not found" in data["errors"][0]["message"].lower()


class TestWriteGameFileValidation:
    """Tests for write_game_file syntax validation."""

    async def test_write_gd_file_validates_syntax(self, tmp_godot_project, monkeypatch):
        """write_game_file validates .gd files after writing."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.mcp_server import write_game_file

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
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.mcp_server import write_game_file

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
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)

        from core.mcp_server import write_game_file

        result = await write_game_file(
            file_path="scenes/main.tscn",
            content='[gd_scene]\n\n[node name="Main" type="Node"]',
        )

        assert "OK:" in result
        assert "SYNTAX ERROR" not in result


# ---------------------------------------------------------------------------
# godot_gotchas tests
# ---------------------------------------------------------------------------


class TestGodotGotchas:
    """Tests for the godot_gotchas tool."""

    async def test_gotchas_returns_all(self):
        """godot_gotchas returns all gotchas when no filter."""
        from core.mcp_server import godot_gotchas

        import json

        result = await godot_gotchas(category="", keyword="")
        data = json.loads(result)
        assert data["total"] > 10
        assert len(data["gotchas"]) == data["total"]

    async def test_gotchas_filter_by_category(self):
        """godot_gotchas filters by category."""
        from core.mcp_server import godot_gotchas

        import json

        result = await godot_gotchas(category="rendering", keyword="")
        data = json.loads(result)
        assert data["total"] >= 3
        for g in data["gotchas"]:
            assert g["category"] == "rendering"

    async def test_gotchas_filter_by_keyword(self):
        """godot_gotchas filters by keyword search."""
        from core.mcp_server import godot_gotchas

        import json

        result = await godot_gotchas(category="", keyword="ColorRect")
        data = json.loads(result)
        assert data["total"] >= 1
        assert any("ColorRect" in g["title"] or "ColorRect" in g["problem"] for g in data["gotchas"])

    async def test_gotchas_filter_combined(self):
        """godot_gotchas with category AND keyword."""
        from core.mcp_server import godot_gotchas

        import json

        result = await godot_gotchas(category="api", keyword="move_and_slide")
        data = json.loads(result)
        assert data["total"] == 1
        assert "move_and_slide" in data["gotchas"][0]["title"]

    async def test_gotchas_no_match(self):
        """godot_gotchas returns empty for non-matching filter."""
        from core.mcp_server import godot_gotchas

        import json

        result = await godot_gotchas(category="nonexistent", keyword="")
        data = json.loads(result)
        assert data["total"] == 0
        assert data["gotchas"] == []

    async def test_gotchas_each_has_required_fields(self):
        """Every gotcha has title, problem, solution, example, category."""
        from core.mcp_server import godot_gotchas, GODOT_GOTCHAS

        for g in GODOT_GOTCHAS:
            assert "title" in g
            assert "problem" in g
            assert "solution" in g
            assert "example" in g
            assert "category" in g


# ---------------------------------------------------------------------------
# gdcheck semantic analysis tests
# ---------------------------------------------------------------------------


class TestGdcheckSemantic:
    """Tests for gdcheck semantic analysis features."""

    async def test_mixed_indentation_detected(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck detects mixed tabs and spaces."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.mcp_server import gdcheck

        # Write file with mixed indentation
        bad_script = "extends Node\n\nfunc _ready():\n\tpass\n    var x = 1"
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "mixed.gd").write_text(bad_script)

        import json

        result = await gdcheck(file_path="scripts/mixed.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "indentation" for i in issues)

    async def test_missing_extends_detected(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck warns about missing extends/class_name."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.mcp_server import gdcheck

        # Script without extends or class_name
        bare_script = "var x = 1\n\nfunc _ready():\n    pass"
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "bare.gd").write_text(bare_script)

        import json

        result = await gdcheck(file_path="scripts/bare.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "structure" for i in issues)

    async def test_large_file_warning(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck warns about files over 300 lines."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.mcp_server import gdcheck

        # Create a 350-line script
        lines = ["extends Node\n"] + ["\nfunc f():\n    pass\n"] * 80
        big_script = "".join(lines)[:350 * 10]  # Ensure >300 lines
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "big.gd").write_text(
            "extends Node\n\n" + "\n".join(f"# line {i}" for i in range(350))
        )

        import json

        result = await gdcheck(file_path="scripts/big.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "maintainability" for i in issues)

    async def test_class_name_cli_warning(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck warns about class_name usage for CLI compatibility."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.mcp_server import gdcheck

        script_with_class = "class_name MyData\nextends RefCounted\n"
        (tmp_godot_project / "scripts").mkdir(exist_ok=True)
        (tmp_godot_project / "scripts" / "mydata.gd").write_text(script_with_class)

        import json

        result = await gdcheck(file_path="scripts/mydata.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        assert any(i["type"] == "cli_compatibility" for i in issues)

    async def test_godot3_api_misuse_detected(
        self, tmp_godot_project, monkeypatch
    ):
        """gdcheck detects Godot 3 API patterns."""
        monkeypatch.setattr("core.mcp_server.GODOT_PROJECT", tmp_godot_project)
        monkeypatch.setattr(
            "core.mcp_server.validator",
            __import__(
                "core.gd_parser", fromlist=["GDScriptValidator"]
            ).GDScriptValidator(project_dir=tmp_godot_project),
        )

        from core.mcp_server import gdcheck

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

        import json

        result = await gdcheck(file_path="scripts/old_api.gd")
        data = json.loads(result)
        issues = data.get("semantic_issues", [])
        api_issues = [i for i in issues if i["type"] == "api_misuse"]
        # Should detect at least: export var, onready var, move_and_slide(args), string connect
        assert len(api_issues) >= 3
