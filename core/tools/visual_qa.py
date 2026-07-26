"""capture_game_screen — Visual QA screenshot capture."""

from __future__ import annotations

import logging

from core.config import mcp, vision

logger = logging.getLogger("godot-mcp")


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
