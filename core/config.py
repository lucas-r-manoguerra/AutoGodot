"""Shared configuration and instances for AutoGodot MCP tools."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Module-level path setup
# ---------------------------------------------------------------------------
_CORE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CORE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.auto_fixer import AutoFixer  # noqa: E402
from core.error_parser import GodotErrorParser  # noqa: E402
from core.gd_parser import GDScriptValidator  # noqa: E402
from core.godot_controller import GodotController  # noqa: E402
from core.scene_builder import SceneBuilder  # noqa: E402
from core.script_builder import ScriptBuilder  # noqa: E402
from core.test_runner import TestRunner  # noqa: E402
from core.vision_qa import VisionQA  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
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
validator = GDScriptValidator(project_dir=GODOT_PROJECT)
error_parser = GodotErrorParser(project_dir=GODOT_PROJECT)
test_runner = TestRunner(godot_path=GODOT_PATH, project_dir=GODOT_PROJECT)
auto_fixer = AutoFixer(project_dir=GODOT_PROJECT)

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "autogodot",
)
