"""AutoGodot MCP Server — stdio transport for AI agent access."""

from __future__ import annotations

import logging
import sys

from core.config import mcp, validator  # noqa: F401

# Import tool modules to register their @mcp.tool() handlers
from core.tools import (  # noqa: F401
    execution,
    visual_qa,
    analysis,
    error_handling,
    knowledge,
)

logger = logging.getLogger("godot-mcp")


def main() -> None:
    """Run the MCP server over stdio transport."""
    logger.info("Starting AutoGodot MCP server (stdio)...")

    # Startup scan: validate all existing .gd files
    try:
        syntax_results = validator.validate_project()
        if syntax_results["invalid_files"] > 0:
            logger.warning(
                "Startup scan found %d files with syntax errors",
                syntax_results["invalid_files"],
            )
            for result in syntax_results["results"]:
                error_msg = result["errors"][0]["message"]
                line_num = result["errors"][0].get("line", 0)
                logger.warning(
                    "  → %s (line %d): %s",
                    result["file"],
                    line_num,
                    error_msg,
                )
        else:
            logger.info(
                "Startup scan: all %d .gd files valid",
                syntax_results["valid_files"],
            )
    except Exception as exc:
        logger.warning("Startup scan failed: %s", exc)

    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as exc:
        logger.critical("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
