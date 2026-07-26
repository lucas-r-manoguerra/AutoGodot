"""
GDScript Validator — Syntax + Semantic checking with gdtoolkit
==============================================================
Provides syntax validation and semantic analysis for .gd files.
Used to validate AI-generated scripts before they reach the user.

Usage:
  - After creating a .gd file via MCP
  - After modifying a .gd file via MCP
  - At project startup to scan existing files
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from gdtoolkit.parser import parser as gd_parser  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class GDScriptValidator:
    """Validates GDScript files using gdtoolkit parser."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()
        logger.info("GDScriptValidator initialized (project: %s)", self.project_dir)

    def validate_file(self, file_path: str) -> dict[str, Any]:
        """Validate a single .gd file for syntax errors.

        Args:
            file_path: Relative path to the .gd file inside the project.

        Returns:
            Dict with keys:
                - valid: bool
                - errors: list of error dicts
                - file: relative path
        """
        target = (self.project_dir / file_path).resolve()

        # Security check
        if not str(target).startswith(str(self.project_dir)):
            return {
                "valid": False,
                "errors": [{"message": "Path traversal not allowed", "line": 0}],
                "file": file_path,
            }

        # Check file exists
        if not target.exists():
            return {
                "valid": False,
                "errors": [{"message": f"File not found: {file_path}", "line": 0}],
                "file": file_path,
            }

        # Only validate .gd files
        if target.suffix != ".gd":
            return {
                "valid": True,
                "errors": [],
                "file": file_path,
            }

        try:
            content = target.read_text(encoding="utf-8")
            return self.validate_content(content, file_path)
        except Exception as exc:
            return {
                "valid": False,
                "errors": [{"message": f"Read error: {exc}", "line": 0}],
                "file": file_path,
            }

    def validate_content(
        self, content: str, file_path: str = "<string>"
    ) -> dict[str, Any]:
        """Validate GDScript content for syntax errors.

        Args:
            content: GDScript source code
            file_path: Optional file path for error reporting

        Returns:
            Dict with keys: valid, errors, file
        """
        try:
            gd_parser.parse(content)
            logger.debug("Syntax OK: %s", file_path)
            return {
                "valid": True,
                "errors": [],
                "file": file_path,
            }
        except Exception as exc:
            error_msg = str(exc)
            line_num = self._extract_line_number(error_msg)

            logger.warning("Syntax error in %s: %s", file_path, error_msg)
            return {
                "valid": False,
                "errors": [{"message": error_msg, "line": line_num}],
                "file": file_path,
            }

    def validate_project(self) -> dict[str, Any]:
        """Validate all .gd files in the project.

        Returns:
            Dict with keys:
                - total_files: int
                - valid_files: int
                - invalid_files: int
                - results: list of per-file results (only invalid ones)
        """
        gd_files = list(self.project_dir.rglob("*.gd"))
        results: list[dict[str, Any]] = []
        valid_count = 0
        invalid_count = 0

        for gd_file in gd_files:
            rel_path = str(gd_file.relative_to(self.project_dir))
            result = self.validate_file(rel_path)

            if result["valid"]:
                valid_count += 1
            else:
                invalid_count += 1
                results.append(result)

        summary = {
            "total_files": len(gd_files),
            "valid_files": valid_count,
            "invalid_files": invalid_count,
            "results": results,
        }

        logger.info(
            "Project validation: %d total, %d valid, %d invalid",
            len(gd_files),
            valid_count,
            invalid_count,
        )
        return summary

    def semantic_checks(self, content: str) -> list[dict[str, Any]]:
        """Run semantic analysis on GDScript content.

        Detects common pitfalls that gdtoolkit parser cannot catch:
        - Mixed indentation (tabs vs spaces)
        - Missing extends/class_name declaration
        - Large monolithic files (>300 lines)
        - class_name CLI compatibility issues
        - Common Godot 3→4 API misuse patterns

        Args:
            content: GDScript source code

        Returns:
            List of issue dicts with keys: type, severity, message
        """
        issues: list[dict[str, Any]] = []
        lines = content.split("\n")

        # 1. Mixed indentation
        has_tabs = any(l.startswith("\t") for l in lines if l.strip())
        has_spaces = any(re.match(r"^    \S", l) for l in lines if l.strip())
        if has_tabs and has_spaces:
            issues.append({
                "type": "indentation",
                "severity": "error",
                "message": "Mixed tabs and spaces — causes parse errors in Godot 4.x",
            })

        # 2. Missing extends/class_name
        if not re.search(r"^(extends|class_name)\s", content, re.MULTILINE):
            issues.append({
                "type": "structure",
                "severity": "warning",
                "message": "Missing 'extends' or 'class_name' declaration",
            })

        # 3. Large monolithic file
        if len(lines) > 300:
            issues.append({
                "type": "maintainability",
                "severity": "warning",
                "message": f"File has {len(lines)} lines — consider splitting (one file = one task)",
            })

        # 4. class_name usage (CLI gotcha)
        class_match = re.search(r"^class_name\s+(\w+)", content, re.MULTILINE)
        if class_match:
            issues.append({
                "type": "cli_compatibility",
                "severity": "info",
                "message": (
                    f"class_name '{class_match.group(1)}' may not resolve in CLI runs. "
                    "Use preload() for more reliable script references."
                ),
            })

        # 5. Common API misuse patterns
        api_patterns = [
            (r"move_and_slide\s*\([^)]+\)", "move_and_slide()",
             "Godot 4.x: move_and_slide() takes NO arguments. Velocity is a property."),
            (r"\.connect\s*\(\s*['\"]", ".connect()",
             "Godot 4.x: Use signal.connect(callable) syntax, not string-based connect."),
            (r"get_tree\(\)\.change_scene\s*\(", "change_scene",
             "Godot 4.x: Use get_tree().change_scene_to_file() or change_scene_to_packed()."),
            (r"\bexport\s+var\b", "export var",
             "Godot 4.x: Use @export annotation, not 'export var' keyword."),
            (r"\bonready\s+var\b", "onready var",
             "Godot 4.x: Use @onready annotation, not 'onready var' keyword."),
        ]
        for pattern, name, msg in api_patterns:
            if re.search(pattern, content):
                issues.append({
                    "type": "api_misuse",
                    "severity": "warning",
                    "message": f"{name}: {msg}",
                })

        return issues

    def _extract_line_number(self, error_msg: str) -> int:
        """Try to extract line number from error message."""
        # Common patterns in gdtoolkit errors
        patterns = [
            r"line (\d+)",
            r"at line (\d+)",
            r"Line (\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                return int(match.group(1))
        return 0
