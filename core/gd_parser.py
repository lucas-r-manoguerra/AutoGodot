"""
GDScript Validator — Syntax checking with gdtoolkit
====================================================
Provides syntax validation for .gd files using gdtoolkit parser.
Used to validate AI-generated scripts before they reach the user.

Usage:
  - After creating a .gd file via MCP
  - After modifying a .gd file via MCP
  - At project startup to scan existing files
"""

from __future__ import annotations

import logging
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

    def _extract_line_number(self, error_msg: str) -> int:
        """Try to extract line number from error message."""
        import re

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
