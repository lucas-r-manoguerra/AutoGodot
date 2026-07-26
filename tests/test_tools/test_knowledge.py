"""Tests for godot_gotchas tool."""

from __future__ import annotations

import json

import pytest


class TestGodotGotchas:
    """Tests for the godot_gotchas tool."""

    async def test_gotchas_returns_all(self):
        """godot_gotchas returns all gotchas when no filter."""
        from core.tools.knowledge import godot_gotchas

        result = await godot_gotchas(category="", keyword="")
        data = json.loads(result)
        assert data["total"] > 10
        assert len(data["gotchas"]) == data["total"]

    async def test_gotchas_filter_by_category(self):
        """godot_gotchas filters by category."""
        from core.tools.knowledge import godot_gotchas

        result = await godot_gotchas(category="rendering", keyword="")
        data = json.loads(result)
        assert data["total"] >= 3
        for g in data["gotchas"]:
            assert g["category"] == "rendering"

    async def test_gotchas_filter_by_keyword(self):
        """godot_gotchas filters by keyword search."""
        from core.tools.knowledge import godot_gotchas

        result = await godot_gotchas(category="", keyword="ColorRect")
        data = json.loads(result)
        assert data["total"] >= 1
        assert any("ColorRect" in g["title"] or "ColorRect" in g["problem"] for g in data["gotchas"])

    async def test_gotchas_filter_combined(self):
        """godot_gotchas with category AND keyword."""
        from core.tools.knowledge import godot_gotchas

        result = await godot_gotchas(category="api", keyword="move_and_slide")
        data = json.loads(result)
        assert data["total"] == 1
        assert "move_and_slide" in data["gotchas"][0]["title"]

    async def test_gotchas_no_match(self):
        """godot_gotchas returns empty for non-matching filter."""
        from core.tools.knowledge import godot_gotchas

        result = await godot_gotchas(category="nonexistent", keyword="")
        data = json.loads(result)
        assert data["total"] == 0
        assert data["gotchas"] == []

    async def test_gotchas_each_has_required_fields(self):
        """Every gotcha has title, problem, solution, example, category."""
        from core.tools.knowledge import GODOT_GOTCHAS

        for g in GODOT_GOTCHAS:
            assert "title" in g
            assert "problem" in g
            assert "solution" in g
            assert "example" in g
            assert "category" in g
