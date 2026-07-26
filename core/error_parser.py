"""
Godot Error Parser — Parse and structure Godot error output
==========================================================
Extracts meaningful error information from Godot's stdout/stderr,
mapping errors to specific files and lines for AI-assisted debugging.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Godot error patterns
# ---------------------------------------------------------------------------

# Main error pattern: ERROR: message -> at: file:line
_RE_ERROR_MAIN = re.compile(
    r"ERROR:\s*(?P<message>.+?)\s*->\s*at:\s*(?P<file>.+?):(?P<line>\d+)",
    re.MULTILINE,
)

# Error without arrow: ERROR: message
_RE_ERROR_SIMPLE = re.compile(
    r"ERROR:\s*(?P<message>.+)",
    re.MULTILINE,
)

# Script error: SCRIPT ERROR: message
_RE_SCRIPT_ERROR = re.compile(
    r"SCRIPT ERROR:\s*(?P<message>.+)",
    re.MULTILINE,
)

# Parse error: Parse Error: message at line X
_RE_PARSE_ERROR = re.compile(
    r"Parse Error:\s*(?P<message>.+?)(?:\s+at\s+line\s+(?P<line>\d+))?$",
    re.MULTILINE,
)

# Stack trace: at function name (file:line)
_RE_STACK_TRACE = re.compile(
    r"at\s+(?:function\s+)?(?P<func>\w+)\s*\((?P<file>.+?):(?P<line>\d+)\)",
    re.MULTILINE,
)

# Warning pattern: WARNING: message
_RE_WARNING = re.compile(
    r"WARNING:\s*(?P<message>.+)",
    re.MULTILINE,
)

# Scene loading error
_RE_SCENE_ERROR = re.compile(
    r"Failed to load.*?(?P<file>[^\s]+\.(?:tscn|tres|gd))",
    re.IGNORECASE,
)


class GodotErrorParser:
    """Parse Godot error output into structured data."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()

    def parse_output(self, stdout: str, stderr: str) -> dict[str, Any]:
        """Parse combined stdout/stderr from Godot.

        Returns:
            Dict with keys:
                - errors: list of error dicts
                - warnings: list of warning strings
                - stack_traces: list of stack trace dicts
                - has_errors: bool
                - summary: human-readable summary
        """
        combined = stdout + "\n" + stderr

        errors = self._extract_errors(combined)
        warnings = self._extract_warnings(combined)
        stack_traces = self._extract_stack_traces(combined)

        has_errors = len(errors) > 0

        summary = self._build_summary(errors, warnings)

        return {
            "errors": errors,
            "warnings": warnings,
            "stack_traces": stack_traces,
            "has_errors": has_errors,
            "summary": summary,
        }

    def _extract_errors(self, output: str) -> list[dict[str, Any]]:
        """Extract structured error information."""
        errors: list[dict[str, Any]] = []
        seen: set[str] = set()

        # Track positions of already-matched errors to avoid duplicates
        matched_positions: list[tuple[int, int]] = []

        # Pattern 1: ERROR: message -> at: file:line
        for match in _RE_ERROR_MAIN.finditer(output):
            file_path = match.group("file")
            line_num = int(match.group("line"))
            message = match.group("message").strip()

            # Normalize file path
            file_path = self._normalize_path(file_path)

            key = f"{file_path}:{line_num}:{message}"
            if key not in seen:
                seen.add(key)
                matched_positions.append((match.start(), match.end()))
                errors.append(
                    {
                        "message": message,
                        "file": file_path,
                        "line": line_num,
                        "type": "error",
                        "source": "godot",
                    }
                )

        # Pattern 2: SCRIPT ERROR: message
        for match in _RE_SCRIPT_ERROR.finditer(output):
            message = match.group("message").strip()
            key = f"script:{message}"
            if key not in seen:
                seen.add(key)
                matched_positions.append((match.start(), match.end()))
                # Try to extract file/line from the message
                file_match = re.search(r"in\s+(.+?):(\d+)", message)
                if file_match:
                    errors.append(
                        {
                            "message": message,
                            "file": self._normalize_path(file_match.group(1)),
                            "line": int(file_match.group(2)),
                            "type": "script_error",
                            "source": "godot",
                        }
                    )
                else:
                    errors.append(
                        {
                            "message": message,
                            "file": "",
                            "line": 0,
                            "type": "script_error",
                            "source": "godot",
                        }
                    )

        # Pattern 3: Parse Error: message at line X
        for match in _RE_PARSE_ERROR.finditer(output):
            message = match.group("message").strip()
            line_str = match.group("line")
            line_num = int(line_str) if line_str else 0
            key = f"parse:{message}:{line_num}"
            if key not in seen:
                seen.add(key)
                matched_positions.append((match.start(), match.end()))
                errors.append(
                    {
                        "message": message,
                        "file": "",
                        "line": line_num,
                        "type": "parse_error",
                        "source": "godot",
                    }
                )

        # Pattern 4: Simple ERROR: message (fallback) — skip if already matched
        for match in _RE_ERROR_SIMPLE.finditer(output):
            # Skip if this position overlaps with an already-matched error
            if any(start <= match.start() < end for start, end in matched_positions):
                continue
            message = match.group("message").strip()
            key = f"simple:{message}"
            if key not in seen:
                seen.add(key)
                errors.append(
                    {
                        "message": message,
                        "file": "",
                        "line": 0,
                        "type": "generic_error",
                        "source": "godot",
                    }
                )

        return errors

    def _extract_warnings(self, output: str) -> list[str]:
        """Extract warning messages."""
        warnings: list[str] = []
        for match in _RE_WARNING.finditer(output):
            warnings.append(match.group("message").strip())
        return warnings

    def _extract_stack_traces(self, output: str) -> list[dict[str, str]]:
        """Extract stack trace information."""
        traces: list[dict[str, str]] = []
        for match in _RE_STACK_TRACE.finditer(output):
            traces.append(
                {
                    "function": match.group("func"),
                    "file": self._normalize_path(match.group("file")),
                    "line": match.group("line"),
                }
            )
        return traces

    def _normalize_path(self, file_path: str) -> str:
        """Normalize a file path relative to project root."""
        # Remove res:// prefix
        if file_path.startswith("res://"):
            file_path = file_path[6:]

        # Remove absolute paths that point to project
        path = Path(file_path)
        try:
            relative = path.relative_to(self.project_dir)
            return str(relative)
        except ValueError:
            # Not relative to project, return as-is
            return file_path

    def _build_summary(self, errors: list[dict[str, Any]], warnings: list[str]) -> str:
        """Build a human-readable error summary."""
        if not errors:
            if warnings:
                return f"No errors. {len(warnings)} warning(s)."
            return "No errors detected."

        lines: list[str] = [f"{len(errors)} error(s) found:"]
        for i, err in enumerate(errors[:10], 1):  # Limit to 10
            location = ""
            if err["file"]:
                location = f" in {err['file']}"
                if err["line"]:
                    location += f":{err['line']}"
            lines.append(f"  {i}. [{err['type']}]{location}: {err['message']}")

        if len(errors) > 10:
            lines.append(f"  ... and {len(errors) - 10} more")

        return "\n".join(lines)
