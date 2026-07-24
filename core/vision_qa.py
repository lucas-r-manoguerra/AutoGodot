"""
Vision QA — Screen capture and visual analysis for Godot games
==============================================================
Captures screenshots of the running Godot game window on Linux
using mss (fast, cross-platform) with Pillow for resizing.

Returns Base64-encoded JPEG suitable for LLM visual QA.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any

try:
    import mss
    import mss.tools
except ImportError:
    mss = None  # type: ignore[assignment]

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class VisionQA:
    """Capture and process game screen for visual QA."""

    def __init__(self) -> None:
        if mss is None:
            logger.warning("mss not installed — screen capture will fail")
        if Image is None:
            logger.warning("Pillow not installed — image resizing will fail")

    async def capture_screen(
        self,
        max_width: int = 1280,
        max_height: int = 720,
        quality: int = 85,
    ) -> dict[str, Any]:
        """Capture the primary monitor and return a resized Base64 JPEG.

        Note: mss captures the full monitor, not a specific window.
        For game-specific capture, the game window should be focused
        and positioned on the target monitor.

        Args:
            max_width: Maximum output width in pixels.
            max_height: Maximum output height in pixels.
            quality: JPEG quality (10-100).

        Returns:
            Dict with keys: base64, width, height, format
        """
        if mss is None:
            raise RuntimeError("mss library not installed. Run: pip install mss")
        if Image is None:
            raise RuntimeError("Pillow library not installed. Run: pip install Pillow")

        logger.info(
            "Capturing screen (max %dx%d, quality=%d)", max_width, max_height, quality
        )

        # Capture the primary monitor
        with mss.mss() as sct:
            # Monitor index 1 = primary monitor (0 = all monitors combined)
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            screenshot = sct.grab(monitor)

            # Convert to PIL Image for resizing
            raw = mss.tools.to_png(screenshot.rgb, screenshot.size)
            img = Image.open(io.BytesIO(raw))  # type: ignore[arg-type]

        original_width, original_height = img.size
        logger.info("Captured %dx%d, resizing...", original_width, original_height)

        # Calculate resize dimensions preserving aspect ratio
        ratio = min(max_width / original_width, max_height / original_height)
        if ratio < 1.0:
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # type: ignore[assignment,union-attr]
        else:
            new_width, new_height = original_width, original_height

        # Encode to JPEG
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
        jpeg_bytes = buffer.getvalue()

        # Base64 encode
        b64_string = base64.b64encode(jpeg_bytes).decode("ascii")

        logger.info(
            "Screen captured: %dx%d → %dx%d (%d bytes JPEG, %d bytes base64)",
            original_width,
            original_height,
            new_width,
            new_height,
            len(jpeg_bytes),
            len(b64_string),
        )

        return {
            "base64": b64_string,
            "width": new_width,
            "height": new_height,
            "format": "jpeg",
        }
