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

import asyncio
import base64
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from mcp.server.mcpserver import MCPServer

# ---------------------------------------------------------------------------
# Module-level imports for subsystems (lazy-loaded to fail gracefully)
# ---------------------------------------------------------------------------
# godot_controller and vision_qa are sibling modules in core/.
# We add the parent dir to sys.path so imports work when running as MCP server.
_CORE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CORE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.godot_controller import GodotController
from core.vision_qa import VisionQA

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

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------
mcp = MCPServer(
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

    scene_path: Optional[str] = Field(
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
        return f"ERROR: Path traversal detected. '{file_path}' escapes the project root."

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

        logger.info("run_godot_test completed: exit=%d duration=%.2fs", result["returncode"], result["duration"])
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
    logger.info("capture_game_screen → max=%dx%d quality=%d", max_width, max_height, quality)

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

        logger.info("capture_screen completed: %dx%d (%d bytes base64)",
                     result["width"], result["height"], len(result["base64"]))
        return str(response)

    except Exception as exc:
        msg = f"ERROR capturing screen: {exc}"
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
