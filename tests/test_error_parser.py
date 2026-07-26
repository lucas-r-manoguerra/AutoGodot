"""Tests for the error parser module."""

from pathlib import Path
import pytest

from core.error_parser import GodotErrorParser


@pytest.fixture
def parser(tmp_path: Path) -> GodotErrorParser:
    """Create a parser instance with a temp project directory."""
    return GodotErrorParser(project_dir=tmp_path)


class TestGodotErrorParser:
    """Test GodotErrorParser."""

    def test_no_errors(self, parser: GodotErrorParser) -> None:
        """Test parsing output with no errors."""
        result = parser.parse_output("Everything is fine\n", "")
        assert result["has_errors"] is False
        assert len(result["errors"]) == 0
        assert "No errors" in result["summary"]

    def test_main_error_pattern(self, parser: GodotErrorParser) -> None:
        """Test parsing ERROR: message -> at: file:line pattern."""
        stderr = "ERROR: Invalid call. Nonexistent function 'foo' in base 'Node' -> at: res://scripts/player.gd:42\n"
        result = parser.parse_output("", stderr)
        assert result["has_errors"] is True
        assert len(result["errors"]) == 1
        assert result["errors"][0]["message"] == "Invalid call. Nonexistent function 'foo' in base 'Node'"
        assert result["errors"][0]["file"] == "scripts/player.gd"
        assert result["errors"][0]["line"] == 42
        assert result["errors"][0]["type"] == "error"

    def test_script_error(self, parser: GodotErrorParser) -> None:
        """Test parsing SCRIPT ERROR: message pattern."""
        stderr = "SCRIPT ERROR: Expected ':' after function signature.\n"
        result = parser.parse_output("", stderr)
        assert result["has_errors"] is True
        assert result["errors"][0]["type"] == "script_error"

    def test_parse_error(self, parser: GodotErrorParser) -> None:
        """Test parsing Parse Error: message at line X pattern."""
        stderr = "Parse Error: Expected ':' at line 15\n"
        result = parser.parse_output("", stderr)
        assert result["has_errors"] is True
        assert result["errors"][0]["type"] == "parse_error"
        assert result["errors"][0]["line"] == 15

    def test_warnings(self, parser: GodotErrorParser) -> None:
        """Test parsing WARNING: messages."""
        stdout = "WARNING: Unused variable 'x' in player.gd\n"
        result = parser.parse_output(stdout, "")
        assert result["has_errors"] is False
        assert len(result["warnings"]) == 1
        assert "Unused variable" in result["warnings"][0]

    def test_stack_traces(self, parser: GodotErrorParser) -> None:
        """Test parsing stack traces."""
        stderr = "at function _ready (scripts/player.gd:10)\nat function _process (scripts/player.gd:25)\n"
        result = parser.parse_output("", stderr)
        assert len(result["stack_traces"]) == 2
        assert result["stack_traces"][0]["function"] == "_ready"
        assert result["stack_traces"][0]["file"] == "scripts/player.gd"
        assert result["stack_traces"][0]["line"] == "10"

    def test_res_protocol_stripped(self, parser: GodotErrorParser) -> None:
        """Test that res:// protocol prefix is stripped."""
        stderr = "ERROR: Something failed -> at: res://scenes/main.tscn:5\n"
        result = parser.parse_output("", stderr)
        assert result["errors"][0]["file"] == "scenes/main.tscn"

    def test_summary_with_errors(self, parser: GodotErrorParser) -> None:
        """Test summary format with errors."""
        stderr = "ERROR: First error -> at: res://a.gd:1\nERROR: Second error -> at: res://b.gd:2\n"
        result = parser.parse_output("", stderr)
        assert "2 error(s) found" in result["summary"]

    def test_summary_no_errors(self, parser: GodotErrorParser) -> None:
        """Test summary format without errors."""
        result = parser.parse_output("", "")
        assert "No errors detected" in result["summary"]

    def test_combined_stdout_stderr(self, parser: GodotErrorParser) -> None:
        """Test parsing both stdout and stderr together."""
        stdout = "Game loaded successfully\n"
        stderr = "ERROR: Missing signal -> at: res://scripts/enemy.gd:15\n"
        result = parser.parse_output(stdout, stderr)
        assert result["has_errors"] is True
        assert len(result["errors"]) == 1

    def test_multiple_error_types(self, parser: GodotErrorParser) -> None:
        """Test parsing multiple error types in one output."""
        stderr = (
            "ERROR: Null reference -> at: res://a.gd:10\n"
            "SCRIPT ERROR: Bad syntax\n"
            "Parse Error: Missing token at line 5\n"
        )
        result = parser.parse_output("", stderr)
        assert result["has_errors"] is True
        assert len(result["errors"]) == 3
        types = {e["type"] for e in result["errors"]}
        assert "error" in types
        assert "script_error" in types
        assert "parse_error" in types
