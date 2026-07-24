"""
AutoGodot — MCP Server
================================
Model Context Protocol server that exposes Godot game development tools
to AI agents (Claude Desktop, VS Code, and other MCP-compatible clients).

Transport: stdio (stdin/stdout)
SDK:       mcp (official Python SDK by Anthropic)

Tools exposed:
  - write_game_file      : Create or edit Godot source files (.gd, .tscn, etc.)
  - run_godot_test       : Launch Godot project and capture console logs
  - capture_game_screen  : Capture a screenshot of the running game (QA Visual)

Environment variables:
  GODOT_PATH   — Path to the Godot 4.x executable (default: "godot4")
  GODOT_PROJECT — Path to the Godot project directory (default: cwd)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Module-level imports for subsystems (lazy-loaded to fail gracefully)
# ---------------------------------------------------------------------------
# godot_controller and vision_qa are sibling modules in core/.
# We add the parent dir to sys.path so imports work when running as MCP server.
_CORE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CORE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.godot_controller import GodotController  # noqa: E402
from core.scene_builder import SceneBuilder  # noqa: E402
from core.script_builder import ScriptBuilder  # noqa: E402
from core.vision_qa import VisionQA  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,  # MCP uses stdout for protocol; logs go to stderr
)
logger = logging.getLogger("godot-mcp")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
GODOT_PATH: str = os.environ.get("GODOT_PATH", "godot4")
GODOT_PROJECT: Path = Path(os.environ.get("GODOT_PROJECT", ".")).resolve()

logger.info("Godot executable : %s", GODOT_PATH)
logger.info("Godot project   : %s", GODOT_PROJECT)

# ---------------------------------------------------------------------------
# Subsystem instances (created once at module load)
# ---------------------------------------------------------------------------
godot = GodotController(godot_path=GODOT_PATH, project_dir=GODOT_PROJECT)
vision = VisionQA()
scene = SceneBuilder(project_dir=GODOT_PROJECT)
script = ScriptBuilder(project_dir=GODOT_PROJECT)

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "autogodot",
)

# ===========================================================================
# Input models (Pydantic — strict typing for MCP tool schemas)
# ===========================================================================


class WriteGameFileInput(BaseModel):
    """Input for creating or editing a Godot source file."""

    file_path: str = Field(
        ...,
        description=(
            "Relative path to the file inside the Godot project directory. "
            "Examples: 'scripts/player.gd', 'scenes/main.tscn', 'addons/my_plugin/plugin.cfg'"
        ),
    )
    content: str = Field(
        ...,
        description="Full text content to write into the file. Overwrites existing content.",
    )
    create_dirs: bool = Field(
        default=True,
        description="If True, create intermediate directories when they don't exist.",
    )


class RunGodotTestInput(BaseModel):
    """Input for running a Godot test scene or script."""

    scene_path: str | None = Field(
        default=None,
        description=(
            "Relative path to a .tscn scene to run. "
            "If omitted, the project's main scene (set in project.godot) is launched."
        ),
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Maximum seconds to wait before force-killing the Godot process.",
    )
    extra_args: list[str] = Field(
        default_factory=list,
        description="Additional CLI arguments to pass to Godot (e.g. ['--verbose']).",
    )


class CaptureGameScreenInput(BaseModel):
    """Input for capturing the game screen for visual QA."""

    max_width: int = Field(
        default=1280,
        ge=320,
        le=3840,
        description="Maximum width in pixels for the resized screenshot.",
    )
    max_height: int = Field(
        default=720,
        ge=240,
        le=2160,
        description="Maximum height in pixels for the resized screenshot.",
    )
    quality: int = Field(
        default=85,
        ge=10,
        le=100,
        description="JPEG compression quality (10–100).",
    )


class ReadSceneInput(BaseModel):
    """Input for reading a .tscn scene file."""

    scene_path: str = Field(
        ...,
        description=(
            "Relative path to the .tscn file inside the Godot project. "
            "Example: 'scenes/main.tscn'"
        ),
    )


class CreateSceneInput(BaseModel):
    """Input for creating a .tscn scene from a JSON definition."""

    scene_path: str = Field(
        ...,
        description=(
            "Relative path where the .tscn will be written. "
            "Example: 'scenes/new_level.tscn'"
        ),
    )
    definition: dict = Field(
        ...,
        description=(
            "Scene definition with keys: nodes (list), resources (list), connections (list). "
            "Each node needs: name, type, parent. Optional: properties, groups, script."
        ),
    )


class ModifySceneInput(BaseModel):
    """Input for modifying an existing .tscn scene."""

    scene_path: str = Field(
        ...,
        description="Relative path to the .tscn file to modify.",
    )
    operations: list[dict] = Field(
        ...,
        description=(
            "List of operations to apply. Each op has 'action' and relevant fields: "
            "add_node: {action, name, type, parent, properties?}, "
            "remove_node: {action, name}, "
            "set_property: {action, node, property, value}, "
            "connect_signal: {action, signal, from_node, to_node, to_method}"
        ),
    )


class ReadScriptInput(BaseModel):
    """Input for reading a .gd script file."""

    script_path: str = Field(
        ...,
        description=(
            "Relative path to the .gd file inside the Godot project. "
            "Example: 'scripts/player.gd'"
        ),
    )


class CreateScriptInput(BaseModel):
    """Input for creating a .gd script from a JSON definition."""

    script_path: str = Field(
        ...,
        description=(
            "Relative path where the .gd will be written. "
            "Example: 'scripts/player.gd'"
        ),
    )
    definition: dict = Field(
        ...,
        description=(
            "Script definition with keys: extends (required), class_name, "
            "signals (list), variables (list of dicts with name, type, value, export), "
            "functions (list of dicts with name, args, body, return_type)."
        ),
    )


class ModifyScriptInput(BaseModel):
    """Input for modifying an existing .gd script."""

    script_path: str = Field(
        ...,
        description="Relative path to the .gd file to modify.",
    )
    operations: list[dict] = Field(
        ...,
        description=(
            "List of operations to apply. Each op has 'action' and relevant fields: "
            "add_signal: {action, name}, "
            "remove_signal: {action, name}, "
            "add_variable: {action, name, type?, value?, export?}, "
            "remove_variable: {action, name}, "
            "add_function: {action, name, args?, body?, return_type?}, "
            "remove_function: {action, name}, "
            "replace_function_body: {action, name, body}, "
            "set_extends: {action, value}, "
            "set_class_name: {action, value}"
        ),
    )


# ===========================================================================
# Tool implementations
# ===========================================================================


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
        return msg

    except OSError as exc:
        msg = f"ERROR writing {file_path}: {exc}"
        logger.error(msg)
        return msg


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
async def capture_game_screen(
    max_width: int = 1280,
    max_height: int = 720,
    quality: int = 85,
) -> str:
    """Capture a screenshot of the running Godot game window for visual QA.

    Takes a screenshot of the active game window, resizes it to fit within
    the specified dimensions, and returns it as a Base64-encoded JPEG string.

    Use this to visually verify that scenes render correctly, UI layouts
    look as expected, or art assets are placed properly.

    Returns a JSON string with the Base64 image data and metadata.
    """
    logger.info(
        "capture_game_screen → max=%dx%d quality=%d", max_width, max_height, quality
    )

    try:
        result = await vision.capture_screen(
            max_width=max_width,
            max_height=max_height,
            quality=quality,
        )

        # Build a structured response the LLM can parse
        response = {
            "status": "success",
            "width": result["width"],
            "height": result["height"],
            "format": "jpeg",
            "quality": quality,
            "base64_data": result["base64"],
        }

        logger.info(
            "capture_screen completed: %dx%d (%d bytes base64)",
            result["width"],
            result["height"],
            len(result["base64"]),
        )
        return str(response)

    except Exception as exc:
        msg = f"ERROR capturing screen: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def read_scene(scene_path: str) -> str:
    """Read and parse a Godot .tscn scene file into structured JSON.

    Parses the scene file and returns all nodes, resources, connections,
    and header metadata. Use this to inspect the current state of a scene
    before making modifications.

    The scene_path is relative to the Godot project root.
    Example: 'scenes/main.tscn'
    """
    logger.info("read_scene → %s", scene_path)

    try:
        parsed = scene.read(scene_path)
        return str(parsed)

    except Exception as exc:
        msg = f"ERROR reading scene: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def create_scene(scene_path: str, definition: dict) -> str:
    """Create a new .tscn scene file from a JSON definition.

    Generates a valid Godot scene file with the specified nodes, resources,
    and signal connections.

    The definition should include:
    - nodes: list of node dicts with name, type, parent, optional properties
    - resources: (optional) list of resource dicts with id, type, properties
    - connections: (optional) list of signal connection dicts

    The scene_path is relative to the Godot project root.
    Example: 'scenes/new_level.tscn'
    """
    logger.info(
        "create_scene → %s (nodes=%d)", scene_path, len(definition.get("nodes", []))
    )

    try:
        created_path = scene.create(scene_path, definition)
        return f"Scene created: {created_path}"

    except Exception as exc:
        msg = f"ERROR creating scene: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def modify_scene(scene_path: str, operations: list[dict]) -> str:
    """Modify an existing .tscn scene file with surgical operations.

    Apply multiple operations in sequence to an existing scene:
    - add_node: {action: 'add_node', name, type, parent, properties?: {}}
    - remove_node: {action: 'remove_node', name}
    - set_property: {action: 'set_property', node, property, value}
    - connect_signal: {action: 'connect_signal', signal, from_node, to_node, to_method}

    The scene_path is relative to the Godot project root.
    """
    logger.info("modify_scene → %s (ops=%d)", scene_path, len(operations))

    try:
        result = scene.modify(scene_path, operations)
        return result

    except Exception as exc:
        msg = f"ERROR modifying scene: {exc}"
        logger.error(msg)
        return msg


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
        return result

    except Exception as exc:
        msg = f"ERROR modifying script: {exc}"
        logger.error(msg)
        return msg


# ===========================================================================
# Entry point
# ===========================================================================


def main() -> None:
    """Run the MCP server over stdio transport."""
    logger.info("Starting AutoGodot MCP server (stdio)...")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as exc:
        logger.critical("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
