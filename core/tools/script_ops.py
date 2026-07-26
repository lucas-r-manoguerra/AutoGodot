"""read_script, create_script, modify_script — GDScript file operations."""

from __future__ import annotations

import logging

from core.config import GODOT_PROJECT, auto_fixer, mcp, script, validator

logger = logging.getLogger("godot-mcp")


@mcp.tool()
async def read_script(script_path: str) -> str:
    """Read and parse a Godot .gd script file into structured JSON.

    Parses the script file and returns all components: extends, class_name,
    signals, variables, functions, and metadata. Use this to inspect the
    current state of a script before making modifications.

    The script_path is relative to the Godot project root.
    Example: 'scripts/player.gd'
    """
    logger.info("read_script → %s", script_path)

    try:
        parsed = script.read(script_path)
        return str(parsed)

    except Exception as exc:
        msg = f"ERROR reading script: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def create_script(script_path: str, definition: dict) -> str:
    """Create a new .gd script file from a JSON definition.

    Generates a valid GDScript file with the specified extends, class_name,
    signals, variables, and functions.

    The definition should include:
    - extends: (required) base class name (e.g., 'Node', 'CharacterBody2D')
    - class_name: (optional) class name for the script
    - signals: (optional) list of signal names or dicts with name/parameters
    - variables: (optional) list of dicts with name, type, value, export
    - functions: (optional) list of dicts with name, args, body, return_type

    The script_path is relative to the Godot project root.
    Example: 'scripts/player.gd'
    """
    logger.info(
        "create_script → %s (functions=%d)",
        script_path,
        len(definition.get("functions", [])),
    )

    try:
        result = script.create(script_path, definition)

        # Auto-fix indentation and issues in generated script
        if script_path.endswith(".gd"):
            fix_result = auto_fixer.fix_errors(script_path, [])
            if fix_result.get("fixed"):
                target = (GODOT_PROJECT / script_path).resolve()
                target.write_text(fix_result["new_content"], encoding="utf-8")
                fixes = "; ".join(fix_result.get("fixes", []))
                result += f"\n🔧 Auto-fixed: {fixes}"

        return result

    except Exception as exc:
        msg = f"ERROR creating script: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def modify_script(script_path: str, operations: list[dict]) -> str:
    """Modify an existing .gd script file with surgical operations.

    Apply multiple operations in sequence to an existing script:
    - add_signal: {action: 'add_signal', name}
    - remove_signal: {action: 'remove_signal', name}
    - add_variable: {action: 'add_variable', name, type?, value?, export?}
    - remove_variable: {action: 'remove_variable', name}
    - add_function: {action: 'add_function', name, args?, body?, return_type?}
    - remove_function: {action: 'remove_function', name}
    - replace_function_body: {action: 'replace_function_body', name, body}
    - set_extends: {action: 'set_extends', value}
    - set_class_name: {action: 'set_class_name', value}

    The script_path is relative to the Godot project root.
    """
    logger.info("modify_script → %s (ops=%d)", script_path, len(operations))

    try:
        result = script.modify(script_path, operations)

        # Validate .gd files for syntax errors after modification
        if script_path.endswith(".gd"):
            validation = validator.validate_file(script_path)
            if not validation["valid"]:
                error_msg = validation["errors"][0]["message"]
                line_num = validation["errors"][0].get("line", 0)
                result += f"\n⚠️ SYNTAX ERROR (line {line_num}): {error_msg}"
                logger.warning(
                    "Syntax error after modify %s: %s", script_path, error_msg
                )

        return result

    except Exception as exc:
        msg = f"ERROR modifying script: {exc}"
        logger.error(msg)
        return msg
