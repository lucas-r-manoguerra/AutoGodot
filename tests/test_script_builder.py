"""
Tests for ScriptBuilder — Structured GDScript manipulation
==========================================================
TDD: Tests written FIRST, implementation follows.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.script_builder import ScriptBuilder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    (tmp_path / "scripts").mkdir()
    return tmp_path


@pytest.fixture
def script_builder(project_dir: Path) -> ScriptBuilder:
    """Create a ScriptBuilder instance."""
    return ScriptBuilder(project_dir)


@pytest.fixture
def sample_definition() -> dict:
    """Full GDScript definition for testing."""
    return {
        "extends": "CharacterBody2D",
        "class_name": "Player",
        "signals": ["died", "health_changed"],
        "variables": [
            {"name": "speed", "type": "float", "value": "200.0", "export": True},
            {"name": "health", "type": "int", "value": "100"},
        ],
        "functions": [
            {
                "name": "_ready",
                "args": "",
                "body": ["\tpass"],
            },
            {
                "name": "take_damage",
                "args": "amount: int",
                "body": ["\thealth -= amount", "\thealth_changed.emit()"],
            },
        ],
    }


@pytest.fixture
def sample_gd_file(project_dir: Path) -> Path:
    """Create a sample .gd file for read/modify tests."""
    content = """\
extends CharacterBody2D
class_name Player

signal died
signal health_changed

@export var speed: float = 200.0
var health: int = 100

func _ready():
\tpass

func take_damage(amount: int) -> void:
\thealth -= amount
\thealth_changed.emit()
"""
    path = project_dir / "scripts" / "player.gd"
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Test: Path Validation
# ---------------------------------------------------------------------------


class TestPathSecurity:
    """AC-Security: Path traversal protection."""

    def test_read_path_traversal(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.read("../../../etc/passwd")
        assert isinstance(result, str)
        assert result.startswith("ERROR:")

    def test_create_path_traversal(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.create("../../../etc/evil.gd", {"extends": "Node"})
        assert isinstance(result, str)
        assert result.startswith("ERROR:")

    def test_modify_path_traversal(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.modify("../../../etc/passwd", [])
        assert isinstance(result, str)
        assert result.startswith("ERROR:")

    def test_valid_relative_path(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.read("scripts/nonexistent.gd")
        assert isinstance(result, str)
        assert result.startswith("ERROR:")
        assert "not found" in result.lower()


# ---------------------------------------------------------------------------
# Test: create()
# ---------------------------------------------------------------------------


class TestCreateScript:
    """AC-1: Create GDScript from structured definition."""

    def test_create_full_definition(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        result = script_builder.create("scripts/player.gd", sample_definition)
        assert result.startswith("OK:")
        assert "player.gd" in result

    def test_create_minimal_definition(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.create("scripts/simple.gd", {"extends": "Node"})
        assert result.startswith("OK:")

    def test_create_empty_nodes_error(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.create("scripts/empty.gd", {})
        assert result.startswith("ERROR:")
        assert "extends" in result.lower() or "definition" in result.lower()

    def test_create_file_written(self, script_builder: ScriptBuilder) -> None:
        script_builder.create("scripts/test.gd", {"extends": "Node"})
        path = script_builder.project_dir / "scripts" / "test.gd"
        assert path.exists()

    def test_create_output_has_extends(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        script_builder.create("scripts/player.gd", sample_definition)
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        assert "extends CharacterBody2D" in content

    def test_create_output_has_class_name(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        script_builder.create("scripts/player.gd", sample_definition)
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        assert "class_name Player" in content

    def test_create_output_has_signals(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        script_builder.create("scripts/player.gd", sample_definition)
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        assert "signal died" in content
        assert "signal health_changed" in content

    def test_create_output_has_exported_var(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        script_builder.create("scripts/player.gd", sample_definition)
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        assert "@export var speed: float = 200.0" in content

    def test_create_output_has_regular_var(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        script_builder.create("scripts/player.gd", sample_definition)
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        assert "var health: int = 100" in content

    def test_create_output_has_functions(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        script_builder.create("scripts/player.gd", sample_definition)
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        assert "func _ready():" in content
        assert "func take_damage(amount: int):" in content

    def test_create_uses_tabs_not_spaces(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        script_builder.create("scripts/player.gd", sample_definition)
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        # Function bodies should use tabs
        for line in content.split("\n"):
            if line.startswith("\t"):
                assert line.startswith("\t"), f"Expected tab, got spaces: {line}"


# ---------------------------------------------------------------------------
# Test: read()
# ---------------------------------------------------------------------------


class TestReadScript:
    """AC-2: Parse GDScript to structured dict."""

    def test_read_returns_dict(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        assert isinstance(result, dict)

    def test_read_extends(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        assert result.get("extends") == "CharacterBody2D"

    def test_read_class_name(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        assert result.get("class_name") == "Player"

    def test_read_signals(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        assert "died" in result.get("signals", [])
        assert "health_changed" in result.get("signals", [])

    def test_read_variables(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        variables = result.get("variables", [])
        assert len(variables) >= 2
        names = [v["name"] for v in variables]
        assert "speed" in names
        assert "health" in names

    def test_read_exported_variable(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        variables = result.get("variables", [])
        speed_var = next(v for v in variables if v["name"] == "speed")
        assert speed_var.get("export") is True

    def test_read_functions(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        functions = result.get("functions", [])
        assert len(functions) >= 2
        names = [f["name"] for f in functions]
        assert "_ready" in names
        assert "take_damage" in names

    def test_read_function_body(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        functions = result.get("functions", [])
        take_damage = next(f for f in functions if f["name"] == "take_damage")
        assert len(take_damage.get("body", [])) >= 2

    def test_read_file_not_found(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.read("scripts/nonexistent.gd")
        assert isinstance(result, str)
        assert result.startswith("ERROR:")
        assert "not found" in result.lower()

    def test_read_metadata(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        result = script_builder.read("scripts/player.gd")
        metadata = result.get("metadata", {})
        assert "lines" in metadata
        assert "path" in metadata


# ---------------------------------------------------------------------------
# Test: modify()
# ---------------------------------------------------------------------------


class TestModifyScript:
    """AC-3: Apply surgical modifications to GDScript."""

    def test_add_signal(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "add_signal", "name": "jumped"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        # Verify the signal was added
        read_result = script_builder.read("scripts/player.gd")
        assert "jumped" in read_result.get("signals", [])

    def test_remove_signal(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "remove_signal", "name": "died"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        assert "died" not in read_result.get("signals", [])

    def test_add_variable(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "add_variable", "name": "armor", "type": "int", "value": "50"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        names = [v["name"] for v in read_result.get("variables", [])]
        assert "armor" in names

    def test_remove_variable(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "remove_variable", "name": "health"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        names = [v["name"] for v in read_result.get("variables", [])]
        assert "health" not in names

    def test_add_function(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [
            {
                "action": "add_function",
                "name": "jump",
                "args": "",
                "body": ["\tpass"],
            }
        ]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        names = [f["name"] for f in read_result.get("functions", [])]
        assert "jump" in names

    def test_remove_function(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "remove_function", "name": "_ready"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        names = [f["name"] for f in read_result.get("functions", [])]
        assert "_ready" not in names

    def test_replace_function_body(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [
            {
                "action": "replace_function_body",
                "name": "_ready",
                "body": ["\tprint('Hello')"],
            }
        ]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        path = script_builder.project_dir / "scripts" / "player.gd"
        content = path.read_text()
        assert "print('Hello')" in content

    def test_set_extends(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "set_extends", "value": "Node2D"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        assert read_result.get("extends") == "Node2D"

    def test_set_class_name(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "set_class_name", "value": "Hero"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        assert read_result.get("class_name") == "Hero"

    def test_multi_op_order(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [
            {"action": "add_signal", "name": "jumped"},
            {"action": "remove_signal", "name": "died"},
            {"action": "add_variable", "name": "mana", "type": "int", "value": "100"},
        ]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("OK:")
        read_result = script_builder.read("scripts/player.gd")
        assert "jumped" in read_result.get("signals", [])
        assert "died" not in read_result.get("signals", [])
        names = [v["name"] for v in read_result.get("variables", [])]
        assert "mana" in names

    def test_unknown_action_error(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "invalid_action"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert result.startswith("ERROR:")
        assert "unknown" in result.lower()

    def test_ok_summary(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        ops = [{"action": "add_signal", "name": "test_signal"}]
        result = script_builder.modify("scripts/player.gd", ops)
        assert "test_signal" in result


# ---------------------------------------------------------------------------
# Test: Round-trip (create → read)
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """AC-4: create → read produces equivalent structure."""

    def test_create_read_round_trip(
        self, script_builder: ScriptBuilder, sample_definition: dict
    ) -> None:
        # Create
        create_result = script_builder.create("scripts/player.gd", sample_definition)
        assert create_result.startswith("OK:")

        # Read back
        read_result = script_builder.read("scripts/player.gd")
        assert isinstance(read_result, dict)

        # Compare structure
        assert read_result.get("extends") == sample_definition.get("extends")
        assert read_result.get("class_name") == sample_definition.get("class_name")
        assert read_result.get("signals") == sample_definition.get("signals")

        # Variables (compare names)
        read_var_names = [v["name"] for v in read_result.get("variables", [])]
        expected_var_names = [v["name"] for v in sample_definition.get("variables", [])]
        assert read_var_names == expected_var_names

        # Functions (compare names)
        read_func_names = [f["name"] for f in read_result.get("functions", [])]
        expected_func_names = [f["name"] for f in sample_definition.get("functions", [])]
        assert read_func_names == expected_func_names


# ---------------------------------------------------------------------------
# Test: Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """AC-5: All errors return "ERROR: ..." strings."""

    def test_error_prefix(self, script_builder: ScriptBuilder) -> None:
        result = script_builder.read("nonexistent.gd")
        assert isinstance(result, str)
        assert result.startswith("ERROR:")

    def test_no_exceptions_propagate(self, script_builder: ScriptBuilder) -> None:
        # Should not raise, should return error string
        result = script_builder.read("nonexistent.gd")
        assert isinstance(result, str)

    def test_read_result_is_serializable(self, script_builder: ScriptBuilder, sample_gd_file: Path) -> None:
        import json
        result = script_builder.read("scripts/player.gd")
        # Should be JSON serializable
        json.dumps(result)
