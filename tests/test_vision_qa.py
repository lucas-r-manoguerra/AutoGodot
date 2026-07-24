"""Tests for VisionQA."""

from __future__ import annotations

import pytest


class TestVisionQACaptureScreen:
    """Tests for VisionQA.capture_screen()."""

    @pytest.mark.usefixtures("mock_screen_capture")
    async def test_capture_screen_success(self, vision_qa):
        """Successful capture returns correct dict structure."""
        result = await vision_qa.capture_screen(
            max_width=1280, max_height=720, quality=85
        )

        assert isinstance(result, dict)
        assert "base64" in result
        assert "width" in result
        assert "height" in result
        assert "format" in result
        assert result["format"] == "jpeg"
        assert isinstance(result["base64"], str)
        assert len(result["base64"]) > 0

    @pytest.mark.usefixtures("mock_screen_capture")
    async def test_capture_screen_resize(self, vision_qa):
        """Resize preserves aspect ratio."""
        result = await vision_qa.capture_screen(
            max_width=800, max_height=600, quality=85
        )

        # Verify dimensions are within bounds
        assert result["width"] <= 800
        assert result["height"] <= 600

    @pytest.mark.usefixtures("mock_screen_capture")
    async def test_capture_screen_quality(self, vision_qa):
        """Quality parameter is passed through."""
        result = await vision_qa.capture_screen(
            max_width=1280, max_height=720, quality=50
        )

        assert result["format"] == "jpeg"
        assert "base64" in result

    async def test_capture_screen_no_mss(self, vision_qa, monkeypatch):
        """RuntimeError when mss is not installed."""
        monkeypatch.setattr("core.vision_qa.mss", None)

        with pytest.raises(RuntimeError, match="mss"):
            await vision_qa.capture_screen()

    async def test_capture_screen_no_pillow(self, vision_qa, monkeypatch):
        """RuntimeError when Pillow is not installed."""
        monkeypatch.setattr("core.vision_qa.Image", None)

        with pytest.raises(RuntimeError, match="Pillow"):
            await vision_qa.capture_screen()
