"""godot_errors and auto_fix — Error parsing and auto-repair tools."""

from __future__ import annotations

import json
import logging

from core.config import auto_fixer, error_parser, mcp

logger = logging.getLogger("godot-mcp")


@mcp.tool()
async def godot_errors(stdout: str = "", stderr: str = "") -> str:
    """Parse Godot error output into structured, actionable information.

    Extracts errors, warnings, stack traces, and maps them to specific files
    and lines. Use this after run_godot_test to understand what went wrong.

    Returns JSON with:
    - errors: list of structured error dicts (message, file, line, type)
    - warnings: list of warning strings
    - stack_traces: list of function/file/line dicts
    - has_errors: bool
    - summary: human-readable error summary
    """
    logger.info(
        "godot_errors → parsing output (stdout=%d, stderr=%d chars)",
        len(stdout),
        len(stderr),
    )

    try:
        result = error_parser.parse_output(stdout, stderr)
        return json.dumps(result, indent=2)

    except Exception as exc:
        msg = f"ERROR parsing Godot output: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def auto_fix(file_path: str) -> str:
    """Automatically fix common GDScript errors in a file.

    Applies fixes for:
    - Mixed indentation (tabs vs spaces)
    - Missing colons after control flow statements
    - Trailing whitespace
    - Common typos (onredy, precess, phisics, etc.)
    - Double spaces

    Returns JSON with:
    - fixed: bool (whether any fixes were applied)
    - fixes: list of applied fix descriptions
    - file_path: str
    - new_content: str (fixed content)
    """
    logger.info("auto_fix → %s", file_path)

    try:
        result = auto_fixer.validate_and_fix(file_path)
        return json.dumps(result, indent=2)

    except Exception as exc:
        msg = f"ERROR auto-fixing: {exc}"
        logger.error(msg)
        return msg
