"""
Test Runner — Execute and parse GdUnit4/Gut test results
=========================================================
Runs automated tests and returns structured results for AI agents.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Test result patterns
# ---------------------------------------------------------------------------

# GdUnit4 patterns
_RE_GDUNIT_PASS = re.compile(r"(\d+)\s+test\(s\)\s+passed")
_RE_GDUNIT_FAIL = re.compile(r"(\d+)\s+test\(s\)\s+failed")
_RE_GDUNIT_ERROR = re.compile(r"ERROR.*?test\s+[\"'](.+?)[\"']\s*(.+)?", re.IGNORECASE)

# Gut patterns
_RE_GUT_PASS = re.compile(r"passes:\s*(\d+)")
_RE_GUT_FAIL = re.compile(r"failures:\s*(\d+)")
_RE_GUT_ASSERT = re.compile(r"(PASSED|FAILED):\s*(.+)")

# Generic test patterns
_RE_TEST_FILE = re.compile(r"(.+?test[_s]?\.gd)", re.IGNORECASE)
_RE_TEST_CLASS = re.compile(r"class_name\s+(\w*Test\w*)", re.IGNORECASE)
_RE_TEST_FUNC = re.compile(r"func\s+test_(\w+)")


class TestRunner:
    """Run and parse automated tests."""

    def __init__(self, godot_path: str, project_dir: Path) -> None:
        self.godot_path = godot_path
        self.project_dir = project_dir.resolve()

    async def run_tests(
        self,
        test_type: str = "gdunit4",
        scene_path: str | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Run tests and return structured results.

        Args:
            test_type: "gdunit4", "gut", or "auto" (auto-detect)
            scene_path: Specific test scene to run
            timeout: Timeout in seconds

        Returns:
            Dict with keys:
                - passed: int
                - failed: int
                - errors: list of error dicts
                - results: list of individual test results
                - summary: human-readable summary
                - duration: float in seconds
        """
        if test_type == "auto":
            test_type = self._detect_test_framework()

        if test_type == "gdunit4":
            return await self._run_gdunit4(scene_path, timeout)
        elif test_type == "gut":
            return await self._run_gut(scene_path, timeout)
        else:
            return {
                "passed": 0,
                "failed": 0,
                "errors": [{"message": f"Unknown test type: {test_type}"}],
                "results": [],
                "summary": f"Unsupported test framework: {test_type}",
                "duration": 0.0,
            }

    def discover_tests(self) -> dict[str, Any]:
        """Discover test files and test functions in the project.

        Returns:
            Dict with keys:
                - test_files: list of test file paths
                - test_classes: list of test class names
                - test_count: total test functions found
        """
        test_files: list[str] = []
        test_classes: list[str] = []
        test_count = 0

        for gd_file in self.project_dir.rglob("*.gd"):
            try:
                content = gd_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Check if file looks like a test
            is_test = bool(_RE_TEST_FILE.search(gd_file.name))
            has_test_class = bool(_RE_TEST_CLASS.search(content))
            has_test_funcs = bool(_RE_TEST_FUNC.search(content))

            if is_test or has_test_class or has_test_funcs:
                rel_path = str(gd_file.relative_to(self.project_dir))
                test_files.append(rel_path)

                # Extract class names
                for match in _RE_TEST_CLASS.finditer(content):
                    test_classes.append(match.group(1))

                # Count test functions
                test_count += len(_RE_TEST_FUNC.findall(content))

        return {
            "test_files": test_files,
            "test_classes": test_classes,
            "test_count": test_count,
        }

    async def _run_gdunit4(
        self, scene_path: str | None, timeout: float
    ) -> dict[str, Any]:
        """Run GdUnit4 tests."""
        # GdUnit4 is typically run via scene
        test_scene = scene_path or "res://tests/tests.tscn"

        cmd = [
            self.godot_path,
            "--headless",
            "--scene",
            test_scene,
            "--quit",
        ]

        result = await self._execute(cmd, timeout)
        return self._parse_gdunit4_output(result)

    async def _run_gut(self, scene_path: str | None, timeout: float) -> dict[str, Any]:
        """Run Gut tests."""
        test_scene = scene_path or "res://tests/tests.tscn"

        cmd = [
            self.godot_path,
            "--headless",
            "--scene",
            test_scene,
            "--quit",
        ]

        result = await self._execute(cmd, timeout)
        return self._parse_gut_output(result)

    def _detect_test_framework(self) -> str:
        """Auto-detect which test framework is installed."""
        addons_dir = self.project_dir / "addons"

        if (addons_dir / "com.gdunit4").exists():
            return "gdunit4"
        if (addons_dir / "gut").exists():
            return "gut"

        # Check for test files
        for gd_file in self.project_dir.rglob("*.gd"):
            try:
                content = gd_file.read_text(encoding="utf-8", errors="replace")
                if "GdUnitSceneRunner" in content or "gdunit4" in content.lower():
                    return "gdunit4"
                if "GutTest" in content or "gut" in content.lower():
                    return "gut"
            except Exception:
                continue

        return "unknown"

    def _parse_gdunit4_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Parse GdUnit4 test output."""
        output = result.get("stdout", "") + "\n" + result.get("stderr", "")

        passed = 0
        failed = 0
        errors: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []

        # Extract pass/fail counts
        pass_match = _RE_GDUNIT_PASS.search(output)
        fail_match = _RE_GDUNIT_FAIL.search(output)

        if pass_match:
            passed = int(pass_match.group(1))
        if fail_match:
            failed = int(fail_match.group(1))

        # Extract individual test errors
        for match in _RE_GDUNIT_ERROR.finditer(output):
            errors.append(
                {
                    "test_name": match.group(1),
                    "message": match.group(2) or "Unknown error",
                }
            )

        # Extract individual assertions
        for match in _RE_GUT_ASSERT.finditer(output):
            results.append(
                {
                    "name": match.group(2),
                    "passed": match.group(1) == "PASSED",
                }
            )

        summary = self._build_test_summary(
            passed, failed, errors, result.get("timed_out", False)
        )

        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "results": results,
            "summary": summary,
            "duration": result.get("duration", 0.0),
            "framework": "gdunit4",
        }

    def _parse_gut_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Parse Gut test output."""
        output = result.get("stdout", "") + "\n" + result.get("stderr", "")

        passed = 0
        failed = 0
        results: list[dict[str, Any]] = []

        # Extract pass/fail counts
        pass_match = _RE_GUT_PASS.search(output)
        fail_match = _RE_GUT_FAIL.search(output)

        if pass_match:
            passed = int(pass_match.group(1))
        if fail_match:
            failed = int(fail_match.group(1))

        # Extract individual assertions
        for match in _RE_GUT_ASSERT.finditer(output):
            results.append(
                {
                    "name": match.group(2),
                    "passed": match.group(1) == "PASSED",
                }
            )

        summary = self._build_test_summary(
            passed, failed, [], result.get("timed_out", False)
        )

        return {
            "passed": passed,
            "failed": failed,
            "errors": [],
            "results": results,
            "summary": summary,
            "duration": result.get("duration", 0.0),
            "framework": "gut",
        }

    def _build_test_summary(
        self,
        passed: int,
        failed: int,
        errors: list[dict[str, Any]],
        timed_out: bool,
    ) -> str:
        """Build human-readable test summary."""
        if timed_out:
            return "Tests timed out."

        total = passed + failed
        if total == 0:
            return "No tests found or no test output detected."

        pass_rate = (passed / total * 100) if total > 0 else 0

        lines: list[str] = [
            f"{total} test(s): {passed} passed, {failed} failed ({pass_rate:.0f}% pass rate)",
        ]

        if errors:
            lines.append("\nFailed tests:")
            for err in errors[:5]:  # Limit to 5
                lines.append(f"  - {err['test_name']}: {err['message']}")
            if len(errors) > 5:
                lines.append(f"  ... and {len(errors) - 5} more failures")

        return "\n".join(lines)

    async def _execute(self, cmd: list[str], timeout: float) -> dict[str, Any]:
        """Execute a command and capture output."""
        start = __import__("time").monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_dir),
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                stdout_bytes = b""
                stderr_bytes = b"[TIMEOUT] Tests timed out\n"

            duration = __import__("time").monotonic() - start

            return {
                "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                "stderr": stderr_bytes.decode("utf-8", errors="replace"),
                "returncode": proc.returncode or -1,
                "duration": duration,
                "timed_out": duration >= timeout,
            }
        except FileNotFoundError:
            return {
                "stdout": "",
                "stderr": f"[ERROR] Godot not found: {self.godot_path}",
                "returncode": -1,
                "duration": 0.0,
                "timed_out": False,
            }
