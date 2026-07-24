---
title: "Add Collisions to Your Game"
type: guide
category: feature
difficulty: beginner
estimated_time: "30-60 minutes"
prerequisites: ["add-physics.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Add Collisions to Your Game

How to set up collision layers, masks, and signals in Godot 4.7.

## Overview

**What you'll learn:**
- Collision layers and masks
- Area2D for triggers
- Collision signals
- Common collision patterns

---

## Collision Layers

### How layers work

- **Layer**: Which layer this object is ON
- **Mask**: Which layers this object DETECTS

Example setup:
- Layer 1: Player
- Layer 2: Enemies
- Layer 3: Collectibles
- Layer 4: Environment

### Setting layers in code

```gdscript
# Player (Layer 1, detects Layers 2, 3, 4)
collision_layer = 1
collision_mask = 2 | 4 | 8  # Layers 2, 3, 4

# Enemy (Layer 2, detects Layers 1, 4)
collision_layer = 2
collision_mask = 1 | 8  # Layers 1, 4

# Coin (Layer 3, detects Layer 1)
collision_layer = 4
collision_mask = 1  # Layer 1
```

### Setting layers in editor

1. Select node
2. Inspector → CollisionObject2D
3. Set Layer (what this object is)
4. Set Mask (what this object detects)

---

## Area2D for Triggers

### Create trigger zone

```gdscript
extends Area2D

signal player_entered
signal player_exited

func _on_body_entered(body: Node2D) -> void:
    if body.name == "Player":
        player_entered.emit()

func _on_body_exited(body: Node2D) -> void:
    if body.name == "Player":
        player_exited.emit()
```

### Create trigger scene

```
[gd_scene load_steps=3]

[ext_resource type="Script" path="res://scripts/trigger.gd" id="1"]

[sub_resource type="RectangleShape2D" id="1"]
size = Vector2(64, 64)

[node name="Trigger" type="Area2D"]
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")
```

---

## Collision Signals

### Body entered/exited

```gdscript
extends CharacterBody2D

func _ready() -> void:
    # Connect signals
    body_entered.connect(_on_body_entered)
    body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("enemies"):
        take_damage(1)

func _on_body_exited(body: Node2D) -> void:
    pass
```

### Area entered/exited

```gdscript
extends Area2D

func _ready() -> void:
    area_entered.connect(_on_area_entered)
    area_exited.connect(_on_area_exited)

func _on_area_entered(area: Area2D) -> void:
    if area.is_in_group("collectibles"):
        area.collect()

func _on_area_exited(area: Area2D) -> void:
    pass
```

---

## Common Patterns

### Player vs Enemy

```gdscript
# Player.gd
func _on_area_entered(area: Area2D) -> void:
    if area.is_in_group("enemy_hitbox"):
        take_damage(area.damage)
        # Invincibility frames
        set_physics_process(false)
        await get_tree().create_timer(1.0).timeout
        set_physics_process(true)
```

### Collectible pickup

```gdscript
# coin.gd
extends Area2D

signal collected(value: int)

@export var value: int = 10

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        collected.emit(value)
        queue_free()
```

### Damage zone

```gdscript
# damage_zone.gd
extends Area2D

@export var damage: int = 1
@export var knockback_force: float = 200.0

func _on_body_entered(body: Node2D) -> void:
    if body.has_method("take_damage"):
        body.take_damage(damage)
    if body is CharacterBody2D:
        var direction = global_position.direction_to(body.global_position)
        body.velocity = -direction * knockback_force
```

---

## Gotchas

1. **Both need collision shapes**: Area2D needs CollisionShape2D to detect
2. **Enable monitoring**: Area2D.monitoring must be true
3. **Groups over names**: Use `is_in_group()` instead of checking names
4. **One-way collisions**: Use for platforms you can jump through from below
5. **Collision layers are bitmasks**: Layer 1 = bit 0, Layer 2 = bit 1, etc.

---

## Cross-References

- [Add Physics Guide](add-physics.md) — Physics bodies and forces
- [Physics Reference](../reference/physics-collision.md) — Complete collision docs
- [Character Checklist](../checklists/character-scene.md) — Ensure completeness
