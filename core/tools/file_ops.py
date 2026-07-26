"""write_game_file — Create or overwrite Godot project files."""

from __future__ import annotations

import logging

from core.config import GODOT_PROJECT, auto_fixer, mcp, validator

logger = logging.getLogger("godot-mcp")


@mcp.tool()
async def write_game_file(
    file_path: str,
    content: str,
    create_dirs: bool = True,
) -> str:
    """Create or overwrite a Godot project file (.gd, .tscn, .tres, .cfg, etc.).

    Use this tool to write GDScript source code, scene definitions, resources,
    or any text-based Godot asset. The file is written relative to the Godot
    project directory configured on this server.

    Returns a confirmation with the absolute path and byte count written.
    """
    logger.info("write_game_file → %s (%d bytes)", file_path, len(content))

    # Resolve against project root and validate no path traversal
    target = (GODOT_PROJECT / file_path).resolve()
    if not str(target).startswith(str(GODOT_PROJECT)):
        return (
            f"ERROR: Path traversal detected. '{file_path}' escapes the project root."
        )

    try:
        # Create parent directories if requested
        if create_dirs:
            target.parent.mkdir(parents=True, exist_ok=True)

        # Write content as UTF-8
        target.write_text(content, encoding="utf-8")
        size = target.stat().st_size

        msg = f"OK: Wrote {size} bytes to {file_path}"
        logger.info(msg)

        # For .gd files: auto-fix then validate
        if file_path.endswith(".gd"):
            # Auto-fix indentation, typos, whitespace
            fix_result = auto_fixer.fix_errors(file_path, [])
            if fix_result.get("fixed"):
                fixed_content = fix_result["new_content"]
                target.write_text(fixed_content, encoding="utf-8")
                size = target.stat().st_size
                fixes = "; ".join(fix_result.get("fixes", []))
                msg += f"\n🔧 Auto-fixed: {fixes}"
                logger.info("Auto-fixed %s: %s", file_path, fixes)

            # Validate syntax
            validation = validator.validate_file(file_path)
            if not validation["valid"]:
                error_msg = validation["errors"][0]["message"]
                line_num = validation["errors"][0].get("line", 0)
                msg += f"\n⚠️ SYNTAX ERROR (line {line_num}): {error_msg}"
                logger.warning("Syntax error in %s: %s", file_path, error_msg)

        return msg

    except OSError as exc:
        msg = f"ERROR writing {file_path}: {exc}"
        logger.error(msg)
        return msg
