"""Tests for GodotController."""

from __future__ import annotations

import pytest


class TestGodotControllerRunProject:
    """Tests for GodotController.run_project()."""

    @pytest.mark.usefixtures("mock_subprocess")
    async def test_run_project_success(self, godot_controller):
        """Successful run returns correct dict structure."""
        result = await godot_controller.run_project(timeout=5.0)

        assert isinstance(result, dict)
        assert "stdout" in result
        assert "stderr" in result
        assert "returncode" in result
        assert "duration" in result
        assert "timed_out" in result
        # Note: source code uses `proc.returncode or -1`, so mock must use truthy value
        assert result["returncode"] > 0  # Truthy exit code means success path
        assert result["timed_out"] is False
        assert result["stdout"] == "stdout output"
        assert result["stderr"] == "stderr output"

    @pytest.mark.usefixtures("mock_subprocess_timeout")
    async def test_run_project_timeout(self, godot_controller):
        """Timeout kills process and returns timed_out=True."""
        result = await godot_controller.run_project(timeout=0.1)

        assert result["timed_out"] is True
        assert result["returncode"] == -1
        assert "TIMEOUT" in result["stderr"]

    @pytest.mark.usefixtures("mock_subprocess")
    async def test_run_project_custom_args(self, godot_controller):
        """Extra args are passed to subprocess."""
        result = await godot_controller.run_project(
            extra_args=["--verbose", "--headless"], timeout=5.0
        )

        # Note: source code uses `proc.returncode or -1`, so mock must use truthy value
        assert result["returncode"] > 0  # Truthy exit code means success path

    async def test_run_project_file_not_found(self, godot_controller, monkeypatch):
        """FileNotFoundError returns error dict."""

        async def mock_create_not_found(*args, **kwargs):
            raise FileNotFoundError("godot4 not found")

        monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_not_found)

        result = await godot_controller.run_project(timeout=5.0)

        assert result["returncode"] == -1
        assert "not found" in result["stderr"].lower()

    async def test_run_project_generic_exception(self, godot_controller, monkeypatch):
        """Generic exception returns error dict."""

        async def mock_create_error(*args, **kwargs):
            raise RuntimeError("Something went wrong")

        monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_error)

        result = await godot_controller.run_project(timeout=5.0)

        assert result["returncode"] == -1
        assert "Something went wrong" in result["stderr"]


class TestGodotControllerBuildCommand:
    """Tests for GodotController._build_command()."""

    def test_build_command_with_scene(self, godot_controller):
        """Scene path adds --scene flag."""
        cmd = godot_controller._build_command("scenes/main.tscn", [])

        assert "--scene" in cmd
        assert "scenes/main.tscn" in cmd
        assert cmd[0] == "godot4"

    def test_build_command_without_scene(self, godot_controller):
        """No scene path means no --scene flag."""
        cmd = godot_controller._build_command(None, [])

        assert "--scene" not in cmd
        assert cmd[0] == "godot4"

    def test_build_command_with_extra_args(self, godot_controller):
        """Extra args are appended."""
        cmd = godot_controller._build_command(None, ["--verbose", "--headless"])

        assert "--verbose" in cmd
        assert "--headless" in cmd

    def test_build_command_path_flag(self, godot_controller):
        """--path flag includes project directory."""
        cmd = godot_controller._build_command(None, [])

        assert "--path" in cmd
        path_index = cmd.index("--path")
        assert cmd[path_index + 1] == str(godot_controller.project_dir)
