---
title: "Build a 2D Platformer"
type: guide
category: build
difficulty: beginner
estimated_time: "2-3 hours"
prerequisites: []
version: "4.7"
created: "2026-07-24"
status: active
---

# Build a 2D Platformer

Step-by-step guide to creating a complete 2D platformer game in Godot 4.7.

## Overview

**What you'll build:**
- Player character with movement and jumping
- Platforms and level design
- Enemies with basic AI
- Collectibles (coins)
- Score and health HUD
- Game over and restart

**Prerequisites:**
- Godot 4.7 installed
- Basic GDScript knowledge

---

## Step 1: Project Setup

### Create project.godot

```ini
; Engine configuration file.
config_version=5

[application]

config/name="2D Platformer"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")

[display]

window/size/viewport_width=1280
window/size/viewport_height=720

[input]

jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"location":0,"echo":false,"script":null)
]
}
move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":97,"location":0,"echo":false,"script":null)
]
}
move_right={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":68,"key_label":0,"unicode":100,"location":0,"echo":false,"script":null)
]
}

[rendering]

renderer/rendering_method="gl_compatibility"
```

### Create folder structure

```
project/
├── scenes/
├── scripts/
├── assets/
│   ├── sprites/
│   ├── audio/
│   └── themes/
```

---

## Step 2: Player Character

### Create player.gd

```gdscript
extends CharacterBody2D

const SPEED = 300.0
const JUMP_VELOCITY = -400.0

var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")
var health: int = 3
var is_dead: bool = false

signal health_changed(new_health: int)
signal player_died

func _physics_process(delta: float) -> void:
    if is_dead:
        return

    # Add gravity
    if not is_on_floor():
        velocity.y += gravity * delta

    # Handle jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    # Horizontal movement
    var direction := Input.get_axis("move_left", "move_right")
    if direction:
        velocity.x = direction * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)

    move_and_slide()

func take_damage(amount: int) -> void:
    health -= amount
    health_changed.emit(health)
    if health <= 0:
        die()

func die() -> void:
    is_dead = true
    player_died.emit()
    # Play death animation, disable collision, etc.
    velocity = Vector2.ZERO
    set_physics_process(false)
```

### Create player.tscn

```
[gd_scene load_steps=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="1"]
size = Vector2(32, 64)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
```

---

## Step 3: Platforms

### Create platform.gd

```gdscript
extends StaticBody2D

# Platforms don't need logic — just collision shape
# Add this script if you want to customize platform behavior
```

### Create platform.tscn

```
[gd_scene load_steps=2]

[sub_resource type="RectangleShape2D" id="1"]
size = Vector2(256, 32)

[node name="Platform" type="StaticBody2D"]

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
```

---

## Step 4: Enemies

### Create enemy.gd

```gdscript
extends CharacterBody2D

const SPEED = 100.0
var direction: int = -1
var health: int = 1
var is_dead: bool = false

signal enemy_died(points: int)

func _physics_process(delta: float) -> void:
    if is_dead:
        return

    # Apply gravity
    if not is_on_floor():
        velocity.y += ProjectSettings.get_setting("physics/2d/default_gravity") * delta

    # Patrol
    velocity.x = direction * SPEED

    # Turn around at walls or edges
    if is_on_wall():
        direction *= -1

    move_and_slide()

func take_damage(amount: int) -> void:
    health -= amount
    if health <= 0:
        die()

func die() -> void:
    is_dead = true
    enemy_died.emit(100)  # Award 100 points
    queue_free()
```

### Create enemy.tscn

```
[gd_scene load_steps=3]

[ext_resource type="Script" path="res://scripts/enemy.gd" id="1"]

[sub_resource type="RectangleShape2D" id="1"]
size = Vector2(32, 32)

[node name="Enemy" type="CharacterBody2D"]
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
```

---

## Step 5: Collectibles

### Create coin.gd

```gdscript
extends Area2D

signal collected(value: int)

@export var value: int = 10

func _on_body_entered(body: Node2D) -> void:
    if body.name == "Player":
        collected.emit(value)
        queue_free()
```

### Create coin.tscn

```
[gd_scene load_steps=3]

[ext_resource type="Script" path="res://scripts/coin.gd" id="1"]

[sub_resource type="CircleShape2D" id="1"]
radius = 16.0

[node name="Coin" type="Area2D"]
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
```

---

## Step 6: HUD

### Create hud.gd

```gdscript
extends CanvasLayer

@onready var score_label: Label = $ScoreLabel
@onready var health_label: Label = $HealthLabel

var score: int = 0

func update_score(points: int) -> void:
    score += points
    score_label.text = "Score: %d" % score

func update_health(health: int) -> void:
    health_label.text = "Health: %d" % health
```

### Create hud.tscn

```
[gd_scene]

[node name="HUD" type="CanvasLayer"]

[node name="ScoreLabel" type="Label" parent="."]
offset_left = 16.0
offset_top = 16.0
offset_right = 200.0
offset_bottom = 40.0
text = "Score: 0"

[node name="HealthLabel" type="Label" parent="."]
offset_left = 16.0
offset_top = 48.0
offset_right = 200.0
offset_bottom = 72.0
text = "Health: 3"
```

---

## Step 7: Main Scene

### Create main.gd

```gdscript
extends Node2D

@onready var player: CharacterBody2D = $Player
@onready var hud: CanvasLayer = $HUD

func _ready() -> void:
    player.health_changed.connect(hud.update_health)
    # Connect enemy signals as they spawn
    # Connect coin signals

func _on_player_player_died() -> void:
    # Game over logic
    get_tree().reload_current_scene()
```

### Create main.tscn

```
[gd_scene load_steps=4]

[ext_resource type="Script" path="res://scripts/main.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="2"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="3"]

[node name="Main" type="Node2D"]
script = ExtResource("1")

[node name="Player" parent="." instance=ExtResource("2")]
position = Vector2(100, 500)

[node name="HUD" parent="." instance=ExtResource("3")]

[node name="Platform" type="StaticBody2D" parent="."]
position = Vector2(640, 600)

[node name="CollisionShape2D" type="CollisionShape2D" parent="Platform"]

[node name="Sprite2D" type="Sprite2D" parent="Platform"]
```

---

## Step 8: Polish

### Add camera follow

```gdscript
# In player.gd, add:
@onready var camera: Camera2D = $Camera2D

func _ready() -> void:
    camera.make_current()
```

### Add death zone

```gdscript
# Create death_zone.gd
extends Area2D

func _on_body_entered(body: Node2D) -> void:
    if body.has_method("take_damage"):
        body.take_damage(999)
```

### Add screen shake

```gdscript
# In main.gd
func shake_screen(intensity: float = 5.0, duration: float = 0.2) -> void:
    var tween := create_tween()
    for i in range(4):
        tween.tween_property($Camera2D, "offset", 
            Vector2(randf_range(-intensity, intensity), 
                    randf_range(-intensity, intensity)), 
            duration / 4)
    tween.tween_property($Camera2D, "offset", Vector2.ZERO, 0.1)
```

---

## Gotchas

1. **Gravity**: Use `ProjectSettings.get_setting("physics/2d/default_gravity")` instead of hardcoding
2. **Delta**: Always multiply physics by `delta` for frame-rate independence
3. **Signals**: Connect signals in `_ready()` or via the editor
4. **Collision layers**: Set up layers properly (player=1, enemies=2, coins=3, platforms=4)
5. **Snap to floor**: Use `move_and_slide()` — it handles floor detection automatically

---

## Next Steps

- Add animations with AnimationPlayer
- Create tilemaps for level design
- Add particle effects (dust, coins)
- Implement saved games
- Add sound effects and music

---

## Cross-References

- [Physics Reference](../reference/physics-collision.md) — Physics bodies and forces
- [Script Patterns](../patterns/scripts.md) — Common GDScript patterns
- [Character Checklist](../checklists/character-scene.md) — Ensure completeness
- [Add AI Guide](add-ai.md) — Enhance enemy behavior
- [Add Collisions Guide](add-collisions.md) — Advanced collision setup
