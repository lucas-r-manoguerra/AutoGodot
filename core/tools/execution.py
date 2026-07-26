"""run_godot_test and run_tests — Execute Godot and test suites."""

from __future__ import annotations

import json
import logging

from core.config import godot, mcp, test_runner

logger = logging.getLogger("godot-mcp")


@mcp.tool()
async def run_godot_test(
    scene_path: str | None = None,
    timeout_seconds: float = 30.0,
    extra_args: list[str] | None = None,
) -> str:
    """Launch the Godot project (or a specific scene) and return console output.

    Runs Godot in headless/debug mode, captures stdout and stderr, and enforces
    a hard timeout. Useful for testing game logic, validating scene loads, or
    checking for runtime errors.

    Returns the combined console output (truncated to 8000 chars) and exit status.
    """
    args = extra_args or []
    target_desc = scene_path or "(main scene)"
    logger.info("run_godot_test → scene=%s timeout=%.1fs", target_desc, timeout_seconds)

    try:
        result = await godot.run_project(
            scene_path=scene_path,
            timeout=timeout_seconds,
            extra_args=args,
        )

        # Truncate output to avoid overwhelming the LLM context
        output = result["stdout"] + result["stderr"]
        if len(output) > 8000:
            output = output[:4000] + "\n... [truncated] ...\n" + output[-4000:]

        status = "SUCCESS" if result["returncode"] == 0 else "FAILED"
        summary = (
            f"--- Godot Test Run [{status}] ---\n"
            f"Scene: {target_desc}\n"
            f"Exit code: {result['returncode']}\n"
            f"Duration: {result['duration']:.2f}s\n"
            f"Timed out: {'yes' if result['timed_out'] else 'no'}\n\n"
            f"--- Console Output ---\n{output}"
        )

        logger.info(
            "run_godot_test completed: exit=%d duration=%.2fs",
            result["returncode"],
            result["duration"],
        )
        return summary

    except Exception as exc:
        msg = f"ERROR running Godot test: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def run_tests(
    test_type: str = "auto",
    scene_path: str | None = None,
    timeout_seconds: float = 60.0,
) -> str:
    """Run automated tests (GdUnit4 or Gut) and return structured results.

    Executes the project's test suite and parses results into a structured
    format with pass/fail counts, individual test results, and a summary.

    Use 'auto' to auto-detect the installed test framework, or specify
    'gdunit4' or 'gut' explicitly.

    Returns JSON with:
    - passed: int
    - failed: int
    - errors: list of failed test details
    - results: list of individual test results
    - summary: human-readable summary
    - duration: float in seconds
    - framework: 'gdunit4' or 'gut'
    """
    logger.info(
        "run_tests → type=%s scene=%s timeout=%.1fs",
        test_type,
        scene_path or "(auto)",
        timeout_seconds,
    )

    try:
        result = await test_runner.run_tests(
            test_type=test_type,
            scene_path=scene_path,
            timeout=timeout_seconds,
        )
        return json.dumps(result, indent=2)

    except Exception as exc:
        msg = f"ERROR running tests: {exc}"
        logger.error(msg)
        return msg
