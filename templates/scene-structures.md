# Scene File Structures

How Godot `.tscn` files are structured and the patterns you need to create them correctly.

## 1. `.tscn` File Anatomy

Every `.tscn` file follows this structure:

```
Header → External Resources → Sub Resources → Nodes
```

### Header

```
[gd_scene load_steps=3 format=3 uid="uid://..."]
```

- `load_steps`: total resources (ext_resource + sub_resource + 1 for the scene root).
- `format=3`: Godot 4.x scene format. Always 3.
- `uid`: optional but recommended — Godot auto-generates it.

### External Resources

Reference files that exist outside this scene (scripts, textures, other scenes):

```
[ext_resource type="Script" path="res://scripts/player.gd" id="1"]
```

- `type`: Godot class name (`Script`, `PackedScene`, `Texture2D`, etc.)
- `path`: project-relative path starting with `res://`
- `id`: numeric string (`"1"`, `"2"`, `"3"`) — never freeform names

### Sub Resources

Inline resources defined inside this scene file:

```
[sub_resource type="RectangleShape2D" id="RectangleShape2D_1"]
size = Vector2(32, 32)
```

### Nodes

Each node in the scene tree:

```
[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Polygon2D" type="Polygon2D" parent="."]
```

- Root node has no `parent`.
- Children use `parent="."` for direct children, `parent="Player"` for nested.

---

## 2. Complete Character Scene

A `CharacterBody2D` with a visual, collision shape, and script:

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

Key points:
- Root node is the `CharacterBody2D`.
- `script = ExtResource("1")` attaches the GDScript.
- Collision shape uses `SubResource()` to reference the inline shape.

---

## 3. Complete UI Scene

A `CanvasLayer` with `Label` children:

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

[node name="HealthLabel" type="Label" parent="."]
offset_left = 20.0
offset_top = 60.0
offset_right = 250.0
offset_bottom = 90.0
text = "Health: 100"
```

Key points:
- `CanvasLayer` renders on a separate layer — UI stays on screen regardless of camera.
- Labels use `offset_*` properties for positioning (not `position`).
- No sub_resources needed when there are no shapes or custom resources.

---

## 4. `ext_resource` ID Convention

Always use **numeric string IDs** for external resources:

```
# Correct
[ext_resource type="Script" path="res://scripts/player.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="2"]

# Wrong
[ext_resource type="Script" path="res://scripts/player.gd" id="player_script"]
```

**Why:**
- Godot's internal parsers auto-assign numeric IDs.
- Consistent format avoids confusion when scenes reference many resources.
- If you use `godot-parser` or similar tools, they expect numeric IDs.

---

## 5. Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Missing `ext_resource` entry | Script or texture silently not loaded | Add the `[ext_resource ...]` block before any `ExtResource("...")` reference |
| ID mismatch | `Unknown resource id` error at load | Ensure the ID in `ExtResource("1")` matches the `id="1"` in the `[ext_resource]` block |
| Wrong property syntax | Scene won't load | Use `script = ExtResource("1")` not `script = "1"` |
| `load_steps` too low | Editor warning or crash | Count: 1 (root) + number of ext_resources + number of sub_resources |
| Wrong `parent` path | Node attaches to wrong parent | Use `"."` for root's direct children, full path like `"Player/Camera2D"` for nested |
| Godot 3.x `format=2` | Won't open in Godot 4.x | Always use `format=3` |
