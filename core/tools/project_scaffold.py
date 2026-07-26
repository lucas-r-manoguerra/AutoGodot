"""gdinit — Project scaffolding tool."""

from __future__ import annotations

import json
import logging

from core.config import GODOT_PROJECT, mcp, scene

logger = logging.getLogger("godot-mcp")

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

PROJECT_GODOT_TEMPLATE_2D = """\
; Engine configuration file.
config_version=5

[application]

config/name="{project_name}"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")

[display]

window/size/viewport_width=1280
window/size/viewport_height=720

[rendering]

renderer/rendering_method="gl_compatibility"
"""

PROJECT_GODOT_TEMPLATE_3D = """\
; Engine configuration file.
config_version=5

[application]

config/name="{project_name}"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")

[display]

window/size/viewport_width=1280
window/size/viewport_height=720

[rendering]

renderer/rendering_method="forward_plus"
"""

PLAYER_SCRIPT_2D = """\
extends CharacterBody2D

const SPEED = 300.0

func _physics_process(_delta: float) -> void:
    var direction := Vector2.ZERO
    direction.x = Input.get_axis("move_left", "move_right")
    direction.y = Input.get_axis("move_up", "move_down")
    if direction.length() > 0:
        direction = direction.normalized()
    velocity = direction * SPEED
    move_and_slide()
"""

PLAYER_SCRIPT_3D = """\
extends CharacterBody3D

const SPEED = 5.0
const JUMP_VELOCITY = 4.5

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y -= gravity * delta
    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY
    var input_dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    if direction:
        velocity.x = direction.x * SPEED
        velocity.z = direction.z * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        velocity.z = move_toward(velocity.z, 0, SPEED)
    move_and_slide()
"""

GAME_MANAGER_SCRIPT = """\
extends Node

signal game_started
signal game_over

var score: int = 0

func start_game() -> void:
    score = 0
    game_started.emit()

func add_score(points: int) -> void:
    score += points

func end_game() -> void:
    game_over.emit()
"""


@mcp.tool()
async def gdinit(project_name: str, project_type: str = "2d") -> str:
    """Initialize a new Godot project with folder structure and base scenes.

    Creates a complete project scaffold including:
    - project.godot configuration file
    - Folder structure (scenes/, scripts/, assets/sprites/, assets/audio/, assets/themes/)
    - Base player scene and script
    - Main scene and script
    - GameManager autoload script

    The project is created inside the configured GODOT_PROJECT directory.
    Use project_type='2d' for 2D games or project_type='3d' for 3D games.

    Returns a JSON summary of created files.
    """
    logger.info("gdinit → name=%s type=%s", project_name, project_type)

    if project_type not in ("2d", "3d"):
        return "ERROR: project_type must be '2d' or '3d'"

    if not project_name.replace("_", "").isalnum():
        return "ERROR: project_name must be snake_case alphanumeric"

    try:
        created_files: list[str] = []

        # 1. Create folder structure
        folders = [
            "scenes",
            "scripts",
            "assets/sprites",
            "assets/audio",
            "assets/themes",
        ]
        for folder in folders:
            folder_path = GODOT_PROJECT / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            created_files.append(f"{folder}/")

        # 2. Create project.godot
        template = (
            PROJECT_GODOT_TEMPLATE_3D
            if project_type == "3d"
            else PROJECT_GODOT_TEMPLATE_2D
        )
        project_godot = template.format(project_name=project_name)
        (GODOT_PROJECT / "project.godot").write_text(project_godot, encoding="utf-8")
        created_files.append("project.godot")

        # 3. Create player script
        player_script = PLAYER_SCRIPT_3D if project_type == "3d" else PLAYER_SCRIPT_2D
        (GODOT_PROJECT / "scripts" / "player.gd").write_text(
            player_script, encoding="utf-8"
        )
        created_files.append("scripts/player.gd")

        # 4. Create game manager script
        (GODOT_PROJECT / "scripts" / "game_manager.gd").write_text(
            GAME_MANAGER_SCRIPT, encoding="utf-8"
        )
        created_files.append("scripts/game_manager.gd")

        # 5. Create player scene
        if project_type == "3d":
            player_scene = {
                "nodes": [
                    {
                        "name": "Player",
                        "type": "CharacterBody3D",
                        "parent": ".",
                        "properties": {"script": "res://scripts/player.gd"},
                    },
                    {
                        "name": "CollisionShape3D",
                        "type": "CollisionShape3D",
                        "parent": "Player",
                    },
                    {
                        "name": "MeshInstance3D",
                        "type": "MeshInstance3D",
                        "parent": "Player",
                    },
                ],
                "resources": [],
                "connections": [],
            }
        else:
            player_scene = {
                "nodes": [
                    {
                        "name": "Player",
                        "type": "CharacterBody2D",
                        "parent": ".",
                        "properties": {"script": "res://scripts/player.gd"},
                    },
                    {
                        "name": "CollisionShape2D",
                        "type": "CollisionShape2D",
                        "parent": "Player",
                    },
                    {"name": "Sprite2D", "type": "Sprite2D", "parent": "Player"},
                ],
                "resources": [],
                "connections": [],
            }
        scene.create("scenes/player.tscn", player_scene)
        created_files.append("scenes/player.tscn")

        # 6. Create main scene
        if project_type == "3d":
            main_scene = {
                "nodes": [
                    {"name": "Main", "type": "Node3D", "parent": "."},
                    {
                        "name": "Player",
                        "type": "CharacterBody3D",
                        "parent": ".",
                        "properties": {"script": "res://scripts/player.gd"},
                    },
                    {
                        "name": "CollisionShape3D",
                        "type": "CollisionShape3D",
                        "parent": "Player",
                    },
                    {
                        "name": "MeshInstance3D",
                        "type": "MeshInstance3D",
                        "parent": "Player",
                    },
                    {
                        "name": "DirectionalLight3D",
                        "type": "DirectionalLight3D",
                        "parent": ".",
                    },
                    {"name": "Camera3D", "type": "Camera3D", "parent": "."},
                ],
                "resources": [],
                "connections": [],
            }
        else:
            main_scene = {
                "nodes": [
                    {
                        "name": "Main",
                        "type": "Node2D",
                        "parent": ".",
                        "properties": {"script": "res://scripts/game_manager.gd"},
                    },
                    {
                        "name": "Player",
                        "type": "CharacterBody2D",
                        "parent": ".",
                        "properties": {"script": "res://scripts/player.gd"},
                    },
                    {
                        "name": "CollisionShape2D",
                        "type": "CollisionShape2D",
                        "parent": "Player",
                    },
                    {"name": "Sprite2D", "type": "Sprite2D", "parent": "Player"},
                    {"name": "Camera2D", "type": "Camera2D", "parent": "Player"},
                ],
                "resources": [],
                "connections": [],
            }
        scene.create("scenes/main.tscn", main_scene)
        created_files.append("scenes/main.tscn")

        response = {
            "status": "success",
            "project_name": project_name,
            "project_type": project_type,
            "files_created": created_files,
            "autoloads": ["GameManager"],
        }
        logger.info("gdinit completed: %d files created", len(created_files))
        return json.dumps(response, indent=2)

    except Exception as exc:
        msg = f"ERROR initializing project: {exc}"
        logger.error(msg)
        return msg
