"""Tests for the test runner module."""

from pathlib import Path
import pytest

from core.test_runner import TestRunner


@pytest.fixture
def runner(tmp_path: Path) -> TestRunner:
    """Create a test runner instance with a temp project directory."""
    return TestRunner(godot_path="/usr/bin/godot", project_dir=tmp_path)


class TestTestRunner:
    """Test TestRunner."""

    def test_discover_no_tests(self, runner: TestRunner) -> None:
        """Test discovering tests when none exist."""
        result = runner.discover_tests()
        assert result["test_files"] == []
        assert result["test_classes"] == []
        assert result["test_count"] == 0

    def test_discover_gdunit4_tests(self, runner: TestRunner) -> None:
        """Test discovering GdUnit4 test files."""
        test_dir = runner.project_dir / "tests"
        test_dir.mkdir()

        test_file = test_dir / "player_test.gd"
        test_file.write_text(
            'extends GdUnitTestSuite\n\nfunc test_move() -> void:\n\tpass\n',
            encoding="utf-8",
        )

        result = runner.discover_tests()
        assert len(result["test_files"]) == 1
        assert "tests/player_test.gd" in result["test_files"]
        assert result["test_count"] == 1

    def test_discover_gut_tests(self, runner: TestRunner) -> None:
        """Test discovering Gut test files."""
        test_dir = runner.project_dir / "tests"
        test_dir.mkdir()

        test_file = test_dir / "test_player.gd"
        test_file.write_text(
            'extends GutTest\n\nfunc test_can_jump() -> void:\n\tassert_true(true)\n',
            encoding="utf-8",
        )

        result = runner.discover_tests()
        assert len(result["test_files"]) == 1
        assert result["test_count"] == 1

    def test_discover_test_class(self, runner: TestRunner) -> None:
        """Test discovering test classes."""
        test_dir = runner.project_dir / "tests"
        test_dir.mkdir()

        test_file = test_dir / "enemy_test.gd"
        test_file.write_text(
            'class_name EnemyTest\nextends GdUnitTestSuite\n',
            encoding="utf-8",
        )

        result = runner.discover_tests()
        assert "EnemyTest" in result["test_classes"]

    def test_discover_multiple_functions(self, runner: TestRunner) -> None:
        """Test counting multiple test functions."""
        test_dir = runner.project_dir / "tests"
        test_dir.mkdir()

        test_file = test_dir / "combat_test.gd"
        test_file.write_text(
            'extends GdUnitTestSuite\n\n'
            'func test_attack() -> void:\n\tpass\n\n'
            'func test_defend() -> void:\n\tpass\n\n'
            'func test_heal() -> void:\n\tpass\n',
            encoding="utf-8",
        )

        result = runner.discover_tests()
        assert result["test_count"] == 3

    def test_auto_detect_gdunit4(self, runner: TestRunner) -> None:
        """Test auto-detecting GdUnit4 framework."""
        addons_dir = runner.project_dir / "addons" / "com.gdunit4"
        addons_dir.mkdir(parents=True)

        detected = runner._detect_test_framework()
        assert detected == "gdunit4"

    def test_auto_detect_gut(self, runner: TestRunner) -> None:
        """Test auto-detecting Gut framework."""
        addons_dir = runner.project_dir / "addons" / "gut"
        addons_dir.mkdir(parents=True)

        detected = runner._detect_test_framework()
        assert detected == "gut"

    def test_auto_detect_unknown(self, runner: TestRunner) -> None:
        """Test auto-detecting when no framework is found."""
        detected = runner._detect_test_framework()
        assert detected == "unknown"

    def test_build_test_summary_no_tests(self, runner: TestRunner) -> None:
        """Test summary with no tests."""
        summary = runner._build_test_summary(0, 0, [], False)
        assert "No tests found" in summary

    def test_build_test_summary_all_pass(self, runner: TestRunner) -> None:
        """Test summary when all tests pass."""
        summary = runner._build_test_summary(5, 0, [], False)
        assert "5 test(s)" in summary
        assert "5 passed" in summary
        assert "0 failed" in summary
        assert "100%" in summary

    def test_build_test_summary_some_fail(self, runner: TestRunner) -> None:
        """Test summary when some tests fail."""
        errors = [{"test_name": "test_attack", "message": "Expected true"}]
        summary = runner._build_test_summary(3, 1, errors, False)
        assert "4 test(s)" in summary
        assert "3 passed" in summary
        assert "1 failed" in summary
        assert "test_attack" in summary

    def test_build_test_summary_timed_out(self, runner: TestRunner) -> None:
        """Test summary when tests timed out."""
        summary = runner._build_test_summary(0, 0, [], True)
        assert "timed out" in summary
