"""Comprehensive tests for SceneBuilder class and MCP scene tools."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.scene_builder import SceneBuilder

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.scene_builder,
]


# ---------------------------------------------------------------------------
# read_scene tests
# ---------------------------------------------------------------------------


class TestReadScene:
    """Tests for SceneBuilder.read()."""

    def test_read_root_node_only(
        self, scene_builder: SceneBuilder, sample_tscn: Path
    ) -> None:
        """AC-1.1: Read scene with root node returns valid structure."""
        result = scene_builder.read("scenes/test_scene.tscn")
        assert isinstance(result, dict)
        assert "header" in result
        assert "nodes" in result
        assert result["header"]["scene_format"] == 3

    def test_read_ext_resources(
        self, scene_builder: SceneBuilder, sample_tscn: Path
    ) -> None:
        """AC-1.2: External resources are parsed."""
        result = scene_builder.read("scenes/test_scene.tscn")
        assert isinstance(result, dict)
        resources = result.get("resources", [])
        assert len(resources) >= 2
        types = [r.get("resource_type") for r in resources]
        assert "Script" in types
        assert "Texture2D" in types

    def test_read_connections(
        self, scene_builder: SceneBuilder, sample_tscn: Path
    ) -> None:
        """AC-1.3: Signal connections are parsed."""
        result = scene_builder.read("scenes/test_scene.tscn")
        assert isinstance(result, dict)
        connections = result.get("connections", [])
        assert len(connections) >= 1
        conn = connections[0]
        assert conn.get("signal") == "died"
        assert conn.get("from_node") == "Player"

    def test_read_groups(self, scene_builder: SceneBuilder, sample_tscn: Path) -> None:
        """AC-1.4: Node groups are parsed."""
        result = scene_builder.read("scenes/test_scene.tscn")
        assert isinstance(result, dict)
        nodes = result.get("nodes", [])
        player_node = next((n for n in nodes if n.get("name") == "Player"), None)
        assert player_node is not None
        groups = player_node.get("groups", [])
        assert "player" in groups
        assert "ally" in groups

    def test_read_file_not_found(self, scene_builder: SceneBuilder) -> None:
        """AC-1.5: Missing file returns ERROR string."""
        result = scene_builder.read("scenes/nonexistent.tscn")
        assert isinstance(result, str)
        assert result.startswith("ERROR")

    def test_read_valid_json(
        self, scene_builder: SceneBuilder, sample_tscn: Path
    ) -> None:
        """AC-1.7: Result can be serialized to valid JSON."""
        result = scene_builder.read("scenes/test_scene.tscn")
        assert isinstance(result, dict)
        serialized = json.dumps(result)
        assert isinstance(serialized, str)
        assert len(serialized) > 0

    def test_read_preserves_node_types(
        self, scene_builder: SceneBuilder, sample_tscn: Path
    ) -> None:
        """Node types are preserved in the parsed result."""
        result = scene_builder.read("scenes/test_scene.tscn")
        assert isinstance(result, dict)
        nodes = result.get("nodes", [])
        types = {n.get("name"): n.get("type") for n in nodes}
        assert types.get("Main") == "Node2D"
        assert types.get("Player") == "CharacterBody2D"
        assert types.get("CollisionShape2D") == "CollisionShape2D"

    def test_read_preserves_parent_paths(
        self, scene_builder: SceneBuilder, sample_tscn: Path
    ) -> None:
        """Parent paths are preserved."""
        result = scene_builder.read("scenes/test_scene.tscn")
        assert isinstance(result, dict)
        nodes = result.get("nodes", [])
        player = next((n for n in nodes if n.get("name") == "Player"), None)
        assert player is not None
        assert player.get("parent") == "."


# ---------------------------------------------------------------------------
# create_scene tests
# ---------------------------------------------------------------------------


class TestCreateScene:
    """Tests for SceneBuilder.create()."""

    def test_create_root_node(
        self, scene_builder: SceneBuilder, tmp_godot_project: Path
    ) -> None:
        """AC-2.1: Create scene with root node."""
        definition = {"nodes": [{"name": "Root", "type": "Node2D"}]}
        result = scene_builder.create("scenes/created.tscn", definition)
        assert isinstance(result, str)
        assert "OK" in result
        assert (tmp_godot_project / "scenes" / "created.tscn").exists()

    def test_create_with_ext_resource(
        self, scene_builder: SceneBuilder, tmp_godot_project: Path
    ) -> None:
        """AC-2.2: Create scene with external resource."""
        definition = {
            "resources": [
                {
                    "type": "ext_resource",
                    "id": "1_abc",
                    "resource_type": "Script",
                    "path": "res://scripts/test.gd",
                }
            ],
            "nodes": [{"name": "Root", "type": "Node2D"}],
        }
        result = scene_builder.create("scenes/with_resource.tscn", definition)
        assert "OK" in result
        scene_file = tmp_godot_project / "scenes" / "with_resource.tscn"
        assert scene_file.exists()
        content = scene_file.read_text()
        assert "ext_resource" in content

    def test_create_with_sub_resource(
        self, scene_builder: SceneBuilder, tmp_godot_project: Path
    ) -> None:
        """AC-2.3: Create scene with sub resource."""
        definition = {
            "sub_resources": [
                {"resource_type": "CircleShape2D", "properties": {"radius": 32.0}}
            ],
            "nodes": [
                {"name": "Root", "type": "Node2D"},
                {"name": "Shape", "type": "CollisionShape2D", "parent": "Root"},
            ],
        }
        result = scene_builder.create("scenes/with_sub.tscn", definition)
        assert "OK" in result
        content = (tmp_godot_project / "scenes" / "with_sub.tscn").read_text()
        assert "sub_resource" in content

    def test_create_nested_nodes(
        self, scene_builder: SceneBuilder, tmp_godot_project: Path
    ) -> None:
        """AC-2.4: Create scene with nested parent."""
        definition = {
            "nodes": [
                {"name": "Root", "type": "Node2D"},
                {"name": "Child", "type": "Sprite2D", "parent": "Root"},
                {"name": "Grandchild", "type": "Node2D", "parent": "Child"},
            ]
        }
        result = scene_builder.create("scenes/nested.tscn", definition)
        assert "OK" in result
        parsed = scene_builder.read("scenes/nested.tscn")
        assert isinstance(parsed, dict)
        names = [n.get("name") for n in parsed.get("nodes", [])]
        assert "Grandchild" in names

    def test_create_with_connections(
        self, scene_builder: SceneBuilder, tmp_godot_project: Path
    ) -> None:
        """AC-2.5: Create scene with signal connections."""
        definition = {
            "nodes": [
                {"name": "Root", "type": "Node2D"},
                {"name": "Button", "type": "Button", "parent": "Root"},
            ],
            "connections": [
                {
                    "signal": "pressed",
                    "from_node": "Button",
                    "to_node": "Root",
                    "to_method": "_on_button_pressed",
                }
            ],
        }
        result = scene_builder.create("scenes/with_conn.tscn", definition)
        assert "OK" in result
        parsed = scene_builder.read("scenes/with_conn.tscn")
        assert isinstance(parsed, dict)
        conns = parsed.get("connections", [])
        assert any(c.get("signal") == "pressed" for c in conns)

    def test_create_returns_ok_message(self, scene_builder: SceneBuilder) -> None:
        """AC-2.7: OK message includes node and resource counts."""
        definition = {
            "nodes": [
                {"name": "Root", "type": "Node2D"},
                {"name": "Child", "type": "Sprite2D", "parent": "Root"},
            ]
        }
        result = scene_builder.create("scenes/ok_msg.tscn", definition)
        assert "OK" in result
        assert "2 node" in result.lower() or "nodes" in result.lower()

    def test_create_empty_nodes_error(self, scene_builder: SceneBuilder) -> None:
        """AC-2.8: Empty nodes list returns ERROR."""
        result = scene_builder.create("scenes/empty.tscn", {"nodes": []})
        assert isinstance(result, str)
        assert result.startswith("ERROR")

    def test_create_file_written_at_path(
        self, scene_builder: SceneBuilder, tmp_godot_project: Path
    ) -> None:
        """AC-2.6: File is created at the specified path."""
        definition = {"nodes": [{"name": "Root", "type": "Node2D"}]}
        scene_builder.create("scenes/verify_path.tscn", definition)
        expected = tmp_godot_project / "scenes" / "verify_path.tscn"
        assert expected.exists()
        assert expected.is_file()


# ---------------------------------------------------------------------------
# modify_scene tests
# ---------------------------------------------------------------------------


class TestModifyScene:
    """Tests for SceneBuilder.modify()."""

    def _create_base_scene(self, scene_builder: SceneBuilder) -> None:
        """Helper: create a base scene for modification tests."""
        definition = {
            "nodes": [
                {"name": "Root", "type": "Node2D"},
                {"name": "Existing", "type": "Sprite2D", "parent": "Root"},
            ]
        }
        scene_builder.create("scenes/modify_test.tscn", definition)

    def test_add_node(self, scene_builder: SceneBuilder) -> None:
        """AC-3.1: Add a node to existing scene."""
        self._create_base_scene(scene_builder)
        ops = [
            {"action": "add_node", "name": "NewNode", "type": "Label", "parent": "Root"}
        ]
        result = scene_builder.modify("scenes/modify_test.tscn", ops)
        assert "OK" in result
        parsed = scene_builder.read("scenes/modify_test.tscn")
        names = [n.get("name") for n in parsed.get("nodes", [])]
        assert "NewNode" in names

    def test_remove_node(self, scene_builder: SceneBuilder) -> None:
        """AC-3.2: Remove a node."""
        self._create_base_scene(scene_builder)
        ops = [{"action": "remove_node", "name": "Existing"}]
        result = scene_builder.modify("scenes/modify_test.tscn", ops)
        assert "OK" in result
        parsed = scene_builder.read("scenes/modify_test.tscn")
        names = [n.get("name") for n in parsed.get("nodes", [])]
        assert "Existing" not in names

    def test_set_property(self, scene_builder: SceneBuilder) -> None:
        """AC-3.3: Set a property on a node."""
        self._create_base_scene(scene_builder)
        ops = [
            {
                "action": "set_property",
                "node": "Root",
                "property": "position",
                "value": "Vector2(50, 100)",
            }
        ]
        result = scene_builder.modify("scenes/modify_test.tscn", ops)
        assert "OK" in result

    def test_connect_signal(self, scene_builder: SceneBuilder) -> None:
        """AC-3.4: Connect a signal."""
        self._create_base_scene(scene_builder)
        ops = [
            {
                "action": "connect_signal",
                "signal": "pressed",
                "from": "Existing",
                "to": "Root",
                "to_method": "_on_pressed",
            }
        ]
        result = scene_builder.modify("scenes/modify_test.tscn", ops)
        assert "OK" in result
        parsed = scene_builder.read("scenes/modify_test.tscn")
        conns = parsed.get("connections", [])
        assert any(c.get("signal") == "pressed" for c in conns)

    def test_remove_root_error(self, scene_builder: SceneBuilder) -> None:
        """AC-3.6: Cannot remove root node."""
        self._create_base_scene(scene_builder)
        ops = [{"action": "remove_node", "name": "Root"}]
        result = scene_builder.modify("scenes/modify_test.tscn", ops)
        assert isinstance(result, str)
        assert result.startswith("ERROR")

    def test_file_not_found_error(self, scene_builder: SceneBuilder) -> None:
        """AC-3.7: Modify missing file returns ERROR."""
        ops = [{"action": "add_node", "name": "X", "type": "Node2D", "parent": "."}]
        result = scene_builder.modify("scenes/missing.tscn", ops)
        assert result.startswith("ERROR")

    def test_multi_op_order(self, scene_builder: SceneBuilder) -> None:
        """AC-3.8: Multiple operations applied in order."""
        self._create_base_scene(scene_builder)
        ops = [
            {"action": "add_node", "name": "Step1", "type": "Node2D", "parent": "Root"},
            {"action": "add_node", "name": "Step2", "type": "Node2D", "parent": "Root"},
            {"action": "remove_node", "name": "Existing"},
        ]
        result = scene_builder.modify("scenes/modify_test.tscn", ops)
        assert "OK" in result
        parsed = scene_builder.read("scenes/modify_test.tscn")
        names = [n.get("name") for n in parsed.get("nodes", [])]
        assert "Step1" in names
        assert "Step2" in names
        assert "Existing" not in names

    def test_ok_summary(self, scene_builder: SceneBuilder) -> None:
        """AC-3.9: OK message includes change summary."""
        self._create_base_scene(scene_builder)
        ops = [{"action": "add_node", "name": "X", "type": "Node2D", "parent": "Root"}]
        result = scene_builder.modify("scenes/modify_test.tscn", ops)
        assert "OK" in result
        assert "added node" in result.lower()


# ---------------------------------------------------------------------------
# Path security tests
# ---------------------------------------------------------------------------


class TestPathSecurity:
    """Tests for path traversal protection (R4)."""

    def test_read_path_traversal(self, scene_builder: SceneBuilder) -> None:
        """AC-4.1: read rejects path traversal."""
        result = scene_builder.read("../../etc/passwd")
        assert isinstance(result, str)
        assert result.startswith("ERROR")

    def test_create_path_traversal(self, scene_builder: SceneBuilder) -> None:
        """AC-4.2: create rejects path traversal."""
        definition = {"nodes": [{"name": "Root", "type": "Node2D"}]}
        result = scene_builder.create("../../etc/evil.tscn", definition)
        assert result.startswith("ERROR")

    def test_modify_path_traversal(self, scene_builder: SceneBuilder) -> None:
        """AC-4.3: modify rejects path traversal."""
        ops = [{"action": "add_node", "name": "X", "type": "Node2D", "parent": "."}]
        result = scene_builder.modify("../../etc/passwd", ops)
        assert result.startswith("ERROR")

    def test_read_escaping_path(self, scene_builder: SceneBuilder) -> None:
        """AC-4.4: read rejects absolute paths outside project."""
        result = scene_builder.read("/etc/passwd")
        assert result.startswith("ERROR")

    def test_valid_relative_path(
        self, scene_builder: SceneBuilder, tmp_godot_project: Path
    ) -> None:
        """AC-4.5: Valid relative path within project works."""
        scenes_dir = tmp_godot_project / "scenes"
        scenes_dir.mkdir()
        (scenes_dir / "ok.tscn").write_text(
            '[gd_scene format=3]\n\n[node name="Root" type="Node2D"]\n',
            encoding="utf-8",
        )
        result = scene_builder.read("scenes/ok.tscn")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling (R5)."""

    def test_error_prefix(self, scene_builder: SceneBuilder) -> None:
        """AC-5.1: All errors start with 'ERROR:'."""
        result = scene_builder.read("nonexistent.tscn")
        assert result.startswith("ERROR:")

    def test_no_exceptions_propagate(self, scene_builder: SceneBuilder) -> None:
        """AC-5.2: No exceptions leak to caller."""
        # Should return ERROR string, not raise
        result = scene_builder.read("../../../escape.tscn")
        assert isinstance(result, str)

    def test_read_result_is_json_serializable(
        self, scene_builder: SceneBuilder, sample_tscn: Path
    ) -> None:
        """AC-5.3: read result can be json.dumps'd without error."""
        result = scene_builder.read("scenes/test_scene.tscn")
        serialized = json.dumps(result)
        assert len(serialized) > 0

    def test_missing_godot_parser_helpful_error(self, tmp_godot_project: Path) -> None:
        """AC-5.4: Missing godot-parser shows helpful error."""
        with patch("core.scene_builder._HAS_GODOT_PARSER", False):
            sb = SceneBuilder(project_dir=tmp_godot_project)
            result = sb.read("any.tscn")
            assert "godot-parser" in result.lower() or "pip install" in result.lower()


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration test: create → read round-trip."""

    def test_create_read_round_trip(self, scene_builder: SceneBuilder) -> None:
        """Create a scene, read it back, verify nodes match."""
        definition = {
            "nodes": [
                {"name": "Root", "type": "Node2D"},
                {
                    "name": "Player",
                    "type": "CharacterBody2D",
                    "parent": "Root",
                    "position": "Vector2(100, 200)",
                },
                {
                    "name": "CollisionShape2D",
                    "type": "CollisionShape2D",
                    "parent": "Player",
                },
            ],
            "connections": [
                {
                    "signal": "died",
                    "from_node": "Player",
                    "to_node": "Root",
                    "to_method": "_on_player_died",
                }
            ],
        }

        # Create
        create_result = scene_builder.create("scenes/roundtrip.tscn", definition)
        assert "OK" in create_result

        # Read back
        parsed = scene_builder.read("scenes/roundtrip.tscn")
        assert isinstance(parsed, dict)

        # Verify node names and types
        nodes = parsed.get("nodes", [])
        node_map = {n["name"]: n for n in nodes}
        assert "Root" in node_map
        assert node_map["Root"]["type"] == "Node2D"
        assert "Player" in node_map
        assert node_map["Player"]["type"] == "CharacterBody2D"

        # Verify connections
        conns = parsed.get("connections", [])
        assert any(c.get("signal") == "died" for c in conns)
