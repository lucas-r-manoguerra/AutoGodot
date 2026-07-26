"""read_scene, create_scene, modify_scene — Scene file operations."""

from __future__ import annotations

import logging

from core.config import mcp, scene

logger = logging.getLogger("godot-mcp")


@mcp.tool()
async def read_scene(scene_path: str) -> str:
    """Read and parse a Godot .tscn scene file into structured JSON.

    Parses the scene file and returns all nodes, resources, connections,
    and header metadata. Use this to inspect the current state of a scene
    before making modifications.

    The scene_path is relative to the Godot project root.
    Example: 'scenes/main.tscn'
    """
    logger.info("read_scene → %s", scene_path)

    try:
        parsed = scene.read(scene_path)
        return str(parsed)

    except Exception as exc:
        msg = f"ERROR reading scene: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def create_scene(scene_path: str, definition: dict) -> str:
    """Create a new .tscn scene file from a JSON definition.

    Generates a valid Godot scene file with the specified nodes, resources,
    and signal connections.

    The definition should include:
    - nodes: list of node dicts with name, type, parent, optional properties
    - resources: (optional) list of resource dicts with id, type, properties
    - connections: (optional) list of signal connection dicts

    The scene_path is relative to the Godot project root.
    Example: 'scenes/new_level.tscn'
    """
    logger.info(
        "create_scene → %s (nodes=%d)", scene_path, len(definition.get("nodes", []))
    )

    try:
        created_path = scene.create(scene_path, definition)
        return f"Scene created: {created_path}"

    except Exception as exc:
        msg = f"ERROR creating scene: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def modify_scene(scene_path: str, operations: list[dict]) -> str:
    """Modify an existing .tscn scene file with surgical operations.

    Apply multiple operations in sequence to an existing scene:
    - add_node: {action: 'add_node', name, type, parent, properties?: {}}
    - remove_node: {action: 'remove_node', name}
    - set_property: {action: 'set_property', node, property, value}
    - connect_signal: {action: 'connect_signal', signal, from_node, to_node, to_method}

    The scene_path is relative to the Godot project root.
    """
    logger.info("modify_scene → %s (ops=%d)", scene_path, len(operations))

    try:
        result = scene.modify(scene_path, operations)
        return result

    except Exception as exc:
        msg = f"ERROR modifying scene: {exc}"
        logger.error(msg)
        return msg
