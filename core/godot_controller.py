"""
Godot Controller — Subprocess management for Godot 4.x
======================================================
Manages isolated Godot processes with strict timeout enforcement,
stdout/stderr capture, and safe termination.

All Godot invocations are non-blocking async with hard kill guarantees.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GodotController:
    """Execute and manage Godot 4.x subprocesses."""

    def __init__(self, godot_path: str, project_dir: Path) -> None:
        self.godot_path = godot_path
        self.project_dir = project_dir.resolve()
        logger.info(
            "GodotController initialized: %s (project: %s)",
            godot_path,
            self.project_dir,
        )

    async def run_project(
        self,
        scene_path: str | None = None,
        timeout: float = 30.0,
        extra_args: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run a Godot scene or the project's main scene.

        Args:
            scene_path: Relative path to a .tscn scene. If None, uses main scene.
            timeout: Hard timeout in seconds before force-kill.
            extra_args: Additional CLI arguments for Godot.

        Returns:
            Dict with keys: stdout, stderr, returncode, duration, timed_out
        """
        cmd = self._build_command(scene_path, extra_args or [])
        logger.info("Executing: %s", " ".join(cmd))

        start = time.monotonic()
        timed_out = False

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_dir),
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                timed_out = True
                logger.warning(
                    "Godot process timed out after %.1fs — killing PID %d",
                    timeout,
                    proc.pid,
                )

                # Hard kill: no graceful shutdown, immediate termination
                proc.kill()
                await proc.wait()

                stdout_bytes = b""
                stderr_bytes = (
                    b"[TIMEOUT] Godot process was force-killed after %.1f seconds\n"
                    % timeout
                )

            duration = time.monotonic() - start

            return {
                "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                "stderr": stderr_bytes.decode("utf-8", errors="replace"),
                "returncode": proc.returncode or -1,
                "duration": duration,
                "timed_out": timed_out,
            }

        except FileNotFoundError:
            duration = time.monotonic() - start
            return {
                "stdout": "",
                "stderr": f"[ERROR] Godot executable not found: {self.godot_path}",
                "returncode": -1,
                "duration": duration,
                "timed_out": False,
            }

        except Exception as exc:
            duration = time.monotonic() - start
            return {
                "stdout": "",
                "stderr": f"[ERROR] {exc}",
                "returncode": -1,
                "duration": duration,
                "timed_out": False,
            }

    def _build_command(
        self, scene_path: str | None, extra_args: list[str]
    ) -> list[str]:
        """Build the Godot CLI command array."""
        cmd = [
            self.godot_path,
            "--path",
            str(self.project_dir),
        ]

        if scene_path:
            cmd.extend(["--scene", scene_path])

        cmd.extend(extra_args)
        return cmd
