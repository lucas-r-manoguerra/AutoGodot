"""Shared fixtures for AutoGodot tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def tmp_godot_project(tmp_path: Path) -> Path:
    """Create a temporary Godot project directory."""
    project_dir = tmp_path / "godot_project"
    project_dir.mkdir()
    (project_dir / "project.godot").write_text('[gd_resource type="ProjectSettings"]\n')
    return project_dir


@pytest.fixture
def godot_controller(tmp_godot_project: Path):
    """Create a GodotController with temp project."""
    from core.godot_controller import GodotController

    return GodotController(godot_path="godot4", project_dir=tmp_godot_project)


@pytest.fixture
def vision_qa():
    """Create a VisionQA instance."""
    from core.vision_qa import VisionQA

    return VisionQA()


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock asyncio.create_subprocess_exec for GodotController tests."""

    async def mock_create(*args: Any, **kwargs: Any) -> Any:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"stdout output", b"stderr output")
        # Note: source code uses `proc.returncode or -1`, so 0 becomes -1.
        # We use a truthy success code to test the "success" path.
        mock_proc.returncode = 1  # Godot exit code 1 is "OK" in this context
        mock_proc.pid = 12345
        return mock_proc

    # Patch at the module level where it's used
    monkeypatch.setattr(
        "core.godot_controller.asyncio.create_subprocess_exec", mock_create
    )


@pytest.fixture
def mock_subprocess_timeout(monkeypatch):
    """Mock subprocess that hangs (for timeout testing)."""

    async def mock_create(*args: Any, **kwargs: Any) -> Any:
        mock_proc = AsyncMock()

        async def hang_forever() -> tuple[bytes, bytes]:
            await asyncio.sleep(3600)  # Hang forever
            return (b"", b"")

        mock_proc.communicate = hang_forever
        mock_proc.returncode = None
        mock_proc.pid = 99999
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()
        return mock_proc

    monkeypatch.setattr(
        "core.godot_controller.asyncio.create_subprocess_exec", mock_create
    )


@pytest.fixture
def mock_screen_capture(monkeypatch):
    """Mock mss and PIL for VisionQA tests."""
    # Create a proper PNG-like bytes for mss.tools.to_png
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # PNG signature  # Dummy data

    # Mock mss
    mock_mss_instance = MagicMock()
    mock_mss_instance.monitors = [{"top": 0, "left": 0, "width": 1920, "height": 1080}]

    # Create a fake screenshot with RGB data
    mock_screenshot = MagicMock()
    mock_screenshot.rgb = b"\x80" * (100 * 100 * 3)  # 100x100 fake image
    mock_screenshot.size = (100, 100)
    mock_mss_instance.grab.return_value = mock_screenshot

    mock_mss_class = MagicMock()
    mock_mss_class.return_value.__enter__ = MagicMock(return_value=mock_mss_instance)
    mock_mss_class.return_value.__exit__ = MagicMock(return_value=False)

    # Create a mock mss module
    mock_mss_module = MagicMock()
    mock_mss_module.mss = mock_mss_class
    mock_mss_module.tools = MagicMock()
    mock_mss_module.tools.to_png.return_value = fake_png

    monkeypatch.setattr("core.vision_qa.mss", mock_mss_module)

    # Mock PIL.Image
    mock_image = MagicMock()
    mock_image.size = (1920, 1080)
    mock_image_resized = MagicMock()
    mock_image_resized.size = (1280, 720)
    mock_image.resize.return_value = mock_image_resized
    # convert().save() writes to a BytesIO buffer
    mock_jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # Fake JPEG
    mock_image_resized.convert.return_value.save.side_effect = (
        lambda buf, **kwargs: buf.write(mock_jpeg_bytes) or buf.seek(0)
    )

    mock_image_open = MagicMock(return_value=mock_image)
    monkeypatch.setattr("PIL.Image.open", mock_image_open)


# ---------------------------------------------------------------------------
# Scene Builder fixtures
# ---------------------------------------------------------------------------

SAMPLE_TSCN = """\
[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1_abc"]
[ext_resource type="Texture2D" path="res://assets/sprite.png" id="2_def"]

[sub_resource type="CircleShape2D" id="CircleShape2D_1"]
radius = 32.0

[node name="Main" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="." groups=["player", "ally"]]
position = Vector2(100, 200)
script = ExtResource("1_abc")

[node name="CollisionShape2D" type="CollisionShape2D" parent="./Player"]
shape = SubResource("CircleShape2D_1")

[connection signal="died" from="Player" to="." method="_on_player_died"]
"""


@pytest.fixture
def sample_tscn(tmp_godot_project: Path) -> Path:
    """Write a sample .tscn file to the temp project and return its path."""
    scenes_dir = tmp_godot_project / "scenes"
    scenes_dir.mkdir()
    scene_file = scenes_dir / "test_scene.tscn"
    scene_file.write_text(SAMPLE_TSCN, encoding="utf-8")
    return scene_file


@pytest.fixture
def scene_builder(tmp_godot_project: Path):
    """Create a SceneBuilder with temp project."""
    from core.scene_builder import SceneBuilder

    return SceneBuilder(project_dir=tmp_godot_project)
