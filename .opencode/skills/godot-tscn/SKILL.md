---
name: godot-tscn
description: "Read, write, and validate Godot .tscn scene files. Triggers on: write scene, create tscn, scene file format, ext_resource, sub_resource, scene structure."
---

# Godot .tscn File Format

How to read, write, and validate Godot 4.x scene files.

## File Structure

Every `.tscn` file has four sections in order:

```
Header → External Resources → Sub Resources → Nodes
```

### Header

```
[gd_scene load_steps=N format=3 uid="uid://..."]
```

- `load_steps` = 1 + ext_resources + sub_resources
- `format=3` — always for Godot 4.x
- `uid` — optional, Godot auto-generates it

### External Resources

Reference files outside this scene (scripts, textures, other scenes):

```
[ext_resource type="Script" path="res://scripts/player.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="2"]
```

Rules:
- `id` must be numeric strings: `"1"`, `"2"`, `"3"`
- Increment sequentially
- Never use freeform names like `"player_script"`

### Sub Resources

Inline resources defined inside the scene:

```
[sub_resource type="RectangleShape2D" id="RectangleShape2D_1"]
size = Vector2(32, 32)
```

### Nodes

```
[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("RectangleShape2D_1")
```

- Root node has no `parent`
- Direct children: `parent="."`
- Nested children: `parent="Player/Camera2D"`

## Writing a Character Scene

```
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="RectangleShape2D_1"]
size = Vector2(32, 32)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Polygon2D" type="Polygon2D" parent="."]
color = Color(0.2, 0.6, 1, 1)
polygon = PackedVector2Array(-16, -16, 16, -16, 16, 16, -16, 16)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("RectangleShape2D_1")
```

## Writing a UI Scene

```
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/game_ui.gd" id="1"]

[node name="GameUI" type="CanvasLayer"]
script = ExtResource("1")

[node name="ScoreLabel" type="Label" parent="."]
offset_left = 20.0
offset_top = 20.0
offset_right = 250.0
offset_bottom = 50.0
text = "Score: 0"
```

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Missing ext_resource entry | Script/texture silently not loaded | Add the `[ext_resource ...]` block |
| ID mismatch | `Unknown resource id` error | Ensure ID in `ExtResource("1")` matches `id="1"` |
| Wrong property syntax | Scene won't load | Use `script = ExtResource("1")` not `script = "1"` |
| load_steps too low | Editor warning | Count: 1 + ext_resources + sub_resources |
| Wrong parent path | Node attaches to wrong parent | Use `"."` for direct children |
| Godot 3 format=2 | Won't open in Godot 4 | Always `format=3` |
