"""
Scene Builder — Structured .tscn manipulation for Godot 4.x
============================================================
Wraps godot-parser to provide read/create/modify operations on .tscn
files using a structured JSON representation instead of raw text.

Tools exposed:
  - read       : Parse a .tscn into structured JSON
  - create     : Build a .tscn from a JSON definition
  - modify     : Apply surgical operations to an existing .tscn
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import godot_parser
    from godot_parser import GDScene, Node

    _HAS_GODOT_PARSER = True
except ImportError:
    godot_parser = None  # type: ignore[assignment]
    GDScene = None  # type: ignore[assignment,misc]
    Node = None  # type: ignore[assignment,misc]
    _HAS_GODOT_PARSER = False

logger = logging.getLogger(__name__)


class SceneBuilder:
    """Structured read/create/modify for Godot 4.x .tscn files."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()
        logger.info("SceneBuilder initialized (project: %s)", self.project_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read(self, scene_path: str) -> dict[str, Any] | str:
        """Parse a .tscn file and return structured JSON.

        Args:
            scene_path: Relative path to the .tscn inside the project.

        Returns:
            Dict with keys: header, resources, nodes, connections.
            On error: returns "ERROR: ..." string.
        """
        if not _HAS_GODOT_PARSER:
            return "ERROR: godot-parser not installed. Run: pip install godot-parser"

        target = self._validate_path(scene_path)
        if isinstance(target, str):
            return target

        if not target.exists():
            return f"ERROR: Scene file not found: {scene_path}"

        try:
            scene = godot_parser.load(str(target))
            return self._scene_to_dict(scene)
        except Exception as exc:
            msg = f"ERROR reading scene {scene_path}: {exc}"
            logger.error(msg)
            return msg

    def create(self, scene_path: str, definition: dict[str, Any]) -> str:
        """Create a .tscn file from a JSON definition.

        Args:
            scene_path: Relative path where the .tscn will be written.
            definition: Scene dict with resources, nodes, connections.

        Returns:
            "OK: ..." message with counts, or "ERROR: ..." string.
        """
        if not _HAS_GODOT_PARSER:
            return "ERROR: godot-parser not installed. Run: pip install godot-parser"

        target = self._validate_path(scene_path)
        if isinstance(target, str):
            return target

        nodes = definition.get("nodes", [])
        if not nodes:
            return "ERROR: Scene must contain at least one node (root)"

        try:
            scene = GDScene()  # type: ignore[call-arg]
            # Set format to 3 (Godot 4.x default)
            scene._sections[0].header["format"] = 3

            # Add external resources
            for res in definition.get("resources", []):
                if res.get("type") == "ext_resource":
                    scene.add_ext_resource(path=res["path"], type=res["resource_type"])

            # Add sub-resources
            for sub in definition.get("sub_resources", []):
                props = sub.get("properties", {})
                scene.add_sub_resource(type=sub["resource_type"], **props)

            # Build node tree
            with scene.use_tree() as tree:
                self._build_tree(tree, nodes)

            # Add connections (stored as sections, not in the tree)
            for conn in definition.get("connections", []):
                header = godot_parser.GDSectionHeader(  # type: ignore[union-attr]
                    "connection",
                    **{
                        "signal": conn["signal"],
                        "from": conn["from_node"],
                        "to": conn["to_node"],
                        "method": conn["to_method"],
                    },
                )
                section = godot_parser.GDSection(header)  # type: ignore[union-attr]
                scene.add_section(section)

            # Ensure parent directory exists
            target.parent.mkdir(parents=True, exist_ok=True)
            scene.write(str(target))

            msg = f"OK: Created scene {scene_path} ({len(nodes)} nodes, {len(definition.get('resources', []))} resources)"
            logger.info(msg)
            return msg

        except Exception as exc:
            msg = f"ERROR creating scene {scene_path}: {exc}"
            logger.error(msg)
            return msg

    def modify(self, scene_path: str, operations: list[dict[str, Any]]) -> str:
        """Apply surgical modifications to an existing .tscn file.

        Args:
            scene_path: Relative path to the .tscn to modify.
            operations: List of operation dicts (add_node, remove_node,
                        set_property, connect_signal, disconnect_signal).

        Returns:
            "OK: ..." message with change summary, or "ERROR: ..." string.
        """
        if not _HAS_GODOT_PARSER:
            return "ERROR: godot-parser not installed. Run: pip install godot-parser"

        target = self._validate_path(scene_path)
        if isinstance(target, str):
            return target

        if not target.exists():
            return f"ERROR: Scene file not found: {scene_path}"

        try:
            scene = godot_parser.load(str(target))  # type: ignore[union-attr]
            changes: list[str] = []

            with scene.use_tree() as tree:
                for op in operations:
                    action = op.get("action", "")
                    if action == "add_node":
                        self._op_add_node(tree, op, changes)
                    elif action == "remove_node":
                        self._op_remove_node(tree, op, changes)
                    elif action == "set_property":
                        self._op_set_property(tree, op, changes)
                    elif action == "connect_signal":
                        self._op_connect_signal(scene, tree, op, changes)
                    elif action == "disconnect_signal":
                        self._op_disconnect_signal(scene, tree, op, changes)
                    else:
                        return f"ERROR: Unknown action: {action}"

            scene.write(str(target))

            summary = "; ".join(changes) if changes else "no changes"
            msg = f"OK: Modified scene {scene_path} — {summary}"
            logger.info(msg)
            return msg

        except Exception as exc:
            msg = f"ERROR modifying scene {scene_path}: {exc}"
            logger.error(msg)
            return msg

    # ------------------------------------------------------------------
    # Path security
    # ------------------------------------------------------------------

    def _validate_path(self, scene_path: str) -> Path | str:
        """Resolve and validate that the path stays inside project_dir.

        Returns:
            Resolved Path on success, or "ERROR: ..." string on failure.
        """
        target = (self.project_dir / scene_path).resolve()
        if not str(target).startswith(str(self.project_dir)):
            return f"ERROR: Path traversal detected. '{scene_path}' escapes the project root."
        return target

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def _scene_to_dict(self, scene: Any) -> dict[str, Any]:
        """Convert a parsed GDScene to the canonical JSON dict."""
        # Header
        header: dict[str, Any] = {
            "godot_version": "4.2",
            "scene_format": 3,
        }
        for section in scene.get_sections():
            if section.header.name == "gd_scene":
                header["scene_format"] = int(section.header.get("format", 3))
                break

        # Resources
        resources: list[dict[str, Any]] = []
        for res in scene.get_ext_resources():
            entry: dict[str, Any] = {
                "type": "ext_resource",
                "id": str(res.id),
                "path": res.path,
                "resource_type": res.type,
            }
            # Preserve uid if present
            uid = res.header.get("uid")
            if uid is not None:
                entry["uid"] = str(uid)
            resources.append(entry)

        for res in scene.get_sub_resources():
            props: dict[str, str] = {}
            for k, v in res.properties.items():
                props[k] = str(v)
            resources.append(
                {
                    "type": "sub_resource",
                    "id": str(res.id),
                    "resource_type": res.type,
                    "properties": props,
                }
            )

        # Nodes
        nodes: list[dict[str, Any]] = []
        for node_section in scene.get_nodes():
            props_node: dict[str, str] = {}
            for k, v in node_section.properties.items():
                props_node[k] = str(v)

            groups = node_section.groups or []

            node_dict: dict[str, Any] = {
                "name": node_section.name,
                "type": node_section.type or "",
                "parent": node_section.parent,
                "properties": props_node,
                "groups": groups,
                "connections": [],
            }
            nodes.append(node_dict)

        # Connections
        connections: list[dict[str, Any]] = []
        for section in scene.get_sections():
            if section.header.name == "connection":
                conn: dict[str, Any] = {
                    "signal": str(section.header.get("signal", "")),
                    "from_node": str(section.header.get("from", "")),
                    "to_node": str(section.header.get("to", "")),
                    "to_method": str(section.header.get("method", "")),
                }
                connections.append(conn)

        # Attach connections to their target nodes
        for conn in connections:
            to_name = conn["to_node"]
            for node in nodes:
                if node["name"] == to_name or (
                    to_name == "." and node["parent"] is None
                ):
                    node["connections"].append(
                        {
                            "signal": conn["signal"],
                            "target": conn["to_node"],
                            "method": conn["to_method"],
                        }
                    )
                    break

        return {
            "header": header,
            "resources": resources,
            "nodes": nodes,
            "connections": connections,
        }

    # ------------------------------------------------------------------
    # Create helpers
    # ------------------------------------------------------------------

    def _build_tree(self, tree: Any, nodes: list[dict[str, Any]]) -> None:
        """Build the node tree from a flat node list.

        Nodes must have the root first (parent=null), then children.
        Parent paths are normalized: "./Child" becomes "Child".
        """
        root_node = None
        child_nodes: list[dict[str, Any]] = []

        for node_def in nodes:
            if node_def.get("parent") is None:
                root_node = node_def
            else:
                # Normalize parent path: "./Child" -> "Child"
                parent_path = node_def["parent"]
                if parent_path.startswith("./"):
                    parent_path = parent_path[2:]
                child_nodes.append({**node_def, "_normalized_parent": parent_path})

        if root_node is None:
            return

        # Create root
        root = Node(
            root_node["name"],
            type=root_node.get("type"),
            groups=root_node.get("groups") or None,
        )
        self._apply_properties(root, root_node.get("properties", {}))
        tree.root = root

        # Create children (assume well-ordered: parents before children)
        for child_def in child_nodes:
            parent_path = child_def["_normalized_parent"]
            parent = tree.get_node(parent_path)
            if parent is None:
                raise ValueError(
                    f"Cannot find parent node {parent_path} of {child_def['name']}"
                )

            child = Node(
                child_def["name"],
                type=child_def.get("type"),
                groups=child_def.get("groups") or None,
            )
            self._apply_properties(child, child_def.get("properties", {}))
            parent.add_child(child)

    def _apply_properties(self, node: Any, properties: dict[str, str]) -> None:
        """Apply property values to a node.

        Uses the Node's properties dict (not section.properties) so that
        flatten() correctly writes them to the GDNodeSection.
        """
        for key, value in properties.items():
            node.properties[key] = value

    # ------------------------------------------------------------------
    # Modify helpers
    # ------------------------------------------------------------------

    def _op_add_node(self, tree: Any, op: dict[str, Any], changes: list[str]) -> None:
        """Add a node to the tree."""
        parent_path = op.get("parent", ".")
        parent = tree.get_node(parent_path)
        if parent is None:
            raise ValueError(f"Parent node not found: {parent_path}")

        name = op.get("name", "")
        node_type = op.get("type", "")
        child = Node(name, type=node_type)  # type: ignore[call-arg]

        # Apply initial properties to the Node's properties dict
        for key, value in (op.get("properties") or {}).items():
            child.properties[key] = value

        parent.add_child(child)
        changes.append(f"added node '{name}'")

    def _op_remove_node(
        self, tree: Any, op: dict[str, Any], changes: list[str]
    ) -> None:
        """Remove a node and its descendants."""
        target_path = op.get("target", "")
        target = tree.get_node(target_path)
        if target is None:
            raise ValueError(f"Node not found: {target_path}")

        # Cannot remove root
        if target is tree.root:
            raise ValueError("Cannot remove root node")

        name = target.name
        target.remove_from_parent()
        changes.append(f"removed node '{name}'")

    def _op_set_property(
        self, tree: Any, op: dict[str, Any], changes: list[str]
    ) -> None:
        """Set a property on a node."""
        target_path = op.get("target", "")
        target = tree.get_node(target_path)
        if target is None:
            raise ValueError(f"Node not found: {target_path}")

        prop = op.get("property", "")
        value = op.get("value", "")
        target.properties[prop] = value
        changes.append(f"set {prop} on '{target_path}'")

    def _op_connect_signal(
        self,
        scene: Any,
        tree: Any,
        op: dict[str, Any],
        changes: list[str],
    ) -> None:
        """Connect a signal between nodes."""
        target_path = op.get("target", "")
        target = tree.get_node(target_path)
        if target is None:
            raise ValueError(f"Node not found: {target_path}")

        signal_name = op.get("signal", "")
        method = op.get("method", "")
        to_node = op.get("to", ".")

        section = godot_parser.GDSection(  # type: ignore[union-attr]
            godot_parser.GDSectionHeader(  # type: ignore[union-attr]
                "connection",
                **{
                    "signal": signal_name,
                    "from": target_path,
                    "to": to_node,
                    "method": method,
                },
            )
        )
        scene.add_section(section)
        changes.append(f"connected '{signal_name}' on '{target_path}'")

    def _op_disconnect_signal(
        self,
        scene: Any,
        tree: Any,
        op: dict[str, Any],
        changes: list[str],
    ) -> None:
        """Disconnect a signal between nodes."""
        target_path = op.get("target", "")
        signal_name = op.get("signal", "")
        method = op.get("method", "")

        for i, section in enumerate(scene.get_sections()):
            if (
                section.header.name == "connection"
                and section.header.get("from") == target_path
                and section.header.get("signal") == signal_name
                and section.header.get("method") == method
            ):
                scene.remove_at(i)
                changes.append(f"disconnected '{signal_name}' on '{target_path}'")
                return

        raise ValueError(
            f"Connection not found: {target_path}.{signal_name} -> {method}"
        )
