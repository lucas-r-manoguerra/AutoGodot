"""
Auto Fix — Automatically fix common GDScript errors
====================================================
Parses error output and attempts automatic corrections.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Common error patterns that can be auto-fixed
# ---------------------------------------------------------------------------

# Missing colon after function/if/elif/else/for/while/class/enum
_RE_MISSING_COLON = re.compile(
    r"(?:function|func|if|elif|else|for|while|class|enum|match|export)\s+.*[^:\s]\s*$"
)

# Wrong indentation (tab vs spaces mix)
_RE_MIXED_INDENT = re.compile(r"^(\t+ | +\t)", re.MULTILINE)

# Trailing whitespace
_RE_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)

# Missing extends (file without extends or class_name)
_RE_NO_EXTENDS = re.compile(r"^(?!.*(?:extends|class_name)\s)")

# Double spaces where single should be
_RE_DOUBLE_SPACE = re.compile(r"  +")

# Wrong arrow for signals (using -> instead of := or =)
_RE_WRONG_ARROW = re.compile(r":\s*->")

# Common typos
_TYPOS = {
    "onredy": "onready",
    "precess": "process",
    "phisics": "physics",
    "velociy": "velocity",
    "positon": "position",
    "rotaion": "rotation",
    "insance": "instance",
    "scne": "scene",
    "scence": "scene",
    "conect": "connect",
    "emit": "emit_signal",
}


class AutoFixer:
    """Automatically fix common GDScript errors."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()

    def fix_errors(
        self, file_path: str, errors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Attempt to fix errors in a file.

        Args:
            file_path: Path to the GDScript file
            errors: List of error dicts from error_parser

        Returns:
            Dict with keys:
                - fixed: bool
                - fixes: list of applied fixes
                - file_path: str
                - new_content: str (if fixed)
        """
        full_path = self.project_dir / file_path
        if not full_path.exists():
            return {
                "fixed": False,
                "fixes": [],
                "file_path": file_path,
                "error": "File not found",
            }

        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "fixed": False,
                "fixes": [],
                "file_path": file_path,
                "error": f"Could not read file: {e}",
            }

        fixes: list[str] = []
        modified = content

        # Apply fixes based on errors
        for error in errors:
            error_type = error.get("type", "")
            message = error.get("message", "")
            line_num = error.get("line", 0)

            # Fix based on error type
            if "indent" in message.lower() or "indent" in error_type:
                result = self._fix_indentation(modified)
                if result != modified:
                    fixes.append("Fixed mixed indentation")
                    modified = result

            if "expected ':'" in message.lower() or "missing ':'" in message.lower():
                result = self._fix_missing_colons(modified)
                if result != modified:
                    fixes.append("Added missing colons")
                    modified = result

            if "expected ':'" in message.lower() and line_num:
                result = self._fix_line_colon(modified, line_num)
                if result != modified:
                    fixes.append(f"Added colon at line {line_num}")
                    modified = result

        # Always apply these common fixes
        result = self._fix_indentation(modified)
        if result != modified:
            fixes.append("Fixed mixed indentation")
            modified = result

        result = self._fix_trailing_whitespace(modified)
        if result != modified:
            fixes.append("Removed trailing whitespace")
            modified = result

        result = self._fix_common_typos(modified)
        if result != modified:
            fixes.append("Fixed common typos")
            modified = result

        result = self._fix_double_spaces(modified)
        if result != modified:
            fixes.append("Fixed double spaces")
            modified = result

        fixed = len(fixes) > 0

        if fixed:
            logger.info("Applied %d fixes to %s", len(fixes), file_path)

        return {
            "fixed": fixed,
            "fixes": fixes,
            "file_path": file_path,
            "new_content": modified if fixed else content,
        }

    def validate_and_fix(self, file_path: str) -> dict[str, Any]:
        """Validate a file and attempt to fix any issues found.

        Returns:
            Dict with keys:
                - valid: bool
                - issues: list of issues found
                - fixes: list of fixes applied
                - file_path: str
        """
        full_path = self.project_dir / file_path
        if not full_path.exists():
            return {
                "valid": False,
                "issues": ["File not found"],
                "fixes": [],
                "file_path": file_path,
            }

        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Could not read file: {e}"],
                "fixes": [],
                "file_path": file_path,
            }

        issues: list[str] = []
        fixes: list[str] = []
        modified = content

        # Check for missing extends/class_name
        if not re.search(r"^(extends|class_name)\s", content, re.MULTILINE):
            issues.append("Missing 'extends' or 'class_name' declaration")

        # Check for mixed indentation
        if _RE_MIXED_INDENT.search(content):
            issues.append("Mixed tabs and spaces in indentation")
            result = self._fix_indentation(modified)
            if result != modified:
                fixes.append("Fixed mixed indentation")
                modified = result

        # Check for trailing whitespace
        if _RE_TRAILING_WS.search(content):
            issues.append("Trailing whitespace found")
            result = self._fix_trailing_whitespace(modified)
            if result != modified:
                fixes.append("Removed trailing whitespace")
                modified = result

        # Check for common typos
        for typo, correction in _TYPOS.items():
            if re.search(rf"\b{typo}\b", content, re.IGNORECASE):
                issues.append(f"Possible typo: '{typo}' -> '{correction}'")
                result = self._fix_common_typos(modified)
                if result != modified:
                    fixes.append(f"Fixed typo: {typo}")
                    modified = result

        valid = len(issues) == 0 or len(fixes) > 0

        return {
            "valid": valid,
            "issues": issues,
            "fixes": fixes,
            "file_path": file_path,
            "new_content": modified if fixes else content,
        }

    def _fix_indentation(self, content: str) -> str:
        """Fix mixed indentation (tabs vs spaces)."""
        lines = content.split("\n")
        fixed_lines: list[str] = []

        for line in lines:
            # Determine indentation style from first indented line
            if line.startswith("\t"):
                # Convert tabs to 4 spaces
                fixed_lines.append(line.replace("\t", "    "))
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def _fix_missing_colons(self, content: str) -> str:
        """Add missing colons after control flow statements."""
        lines = content.split("\n")
        fixed_lines: list[str] = []

        for line in lines:
            stripped = line.rstrip()
            # Check if line ends without colon but should have one
            if _RE_MISSING_COLON.match(stripped) and not stripped.startswith("#") and stripped:
                line = stripped + ":"
            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def _fix_line_colon(self, content: str, line_num: int) -> str:
        """Fix missing colon on a specific line."""
        lines = content.split("\n")
        if 0 < line_num <= len(lines):
            line = lines[line_num - 1]
            stripped = line.rstrip()
            if stripped and not stripped.endswith(":") and not stripped.startswith("#"):
                lines[line_num - 1] = stripped + ":"
        return "\n".join(lines)

    def _fix_trailing_whitespace(self, content: str) -> str:
        """Remove trailing whitespace."""
        return _RE_TRAILING_WS.sub("", content)

    def _fix_common_typos(self, content: str) -> str:
        """Fix common GDScript typos."""
        result = content
        for typo, correction in _TYPOS.items():
            result = re.sub(rf"\b{typo}\b", correction, result, flags=re.IGNORECASE)
        return result

    def _fix_double_spaces(self, content: str) -> str:
        """Fix double spaces (except in strings and indentation)."""
        lines = content.split("\n")
        fixed_lines: list[str] = []

        for line in lines:
            # Skip lines that are comments or strings
            if line.strip().startswith("#") or '"' in line or "'" in line:
                fixed_lines.append(line)
            else:
                # Only fix double spaces that are NOT at the start of the line (indentation)
                stripped = line.lstrip()
                leading = line[: len(line) - len(stripped)]
                fixed_stripped = _RE_DOUBLE_SPACE.sub(" ", stripped)
                fixed_lines.append(leading + fixed_stripped)

        return "\n".join(fixed_lines)
