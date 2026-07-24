---
title: "Build a 2D Top-Down Game"
type: guide
category: build
difficulty: beginner
estimated_time: "2-3 hours"
prerequisites: []
version: "4.7"
created: "2026-07-24"
status: active
---

# Build a 2D Top-Down Game

Step-by-step guide to creating a top-down action/adventure game in Godot 4.7.

## Overview

**What you'll build:**
- Player character with 8-directional movement
- Camera that follows the player
- Enemies with chase AI
- Combat system (melee/ranged)
- Health and damage system
- Simple level with walls

---

## Step 1: Project Setup

### Create project.godot

```ini
config_version=5

[application]

config/name="2D Top-Down"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")

[display]

window/size/viewport_width=1280
window/size/viewport_height=720

[input]

move_up={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":87,"key_label":0,"unicode":119,"location":0,"echo":false,"script":null)
]
}
move_down={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":83,"key_label":0,"unicode":115,"location":0,"echo":false,"script":null)
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
attack={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":74,"key_label":0,"unicode":106,"location":0,"echo":false,"script":null)
]
}

[rendering]

renderer/rendering_method="gl_compatibility"
```

---

## Step 2: Player Character

### Create player.gd

```gdscript
extends CharacterBody2D

const SPEED = 200.0
var health: int = 5
var is_dead: bool = false
var facing: Vector2 = Vector2.DOWN

signal health_changed(new_health: int)
signal player_died

func _physics_process(_delta: float) -> void:
    if is_dead:
        return

    var direction := Vector2.ZERO
    direction.x = Input.get_axis("move_left", "move_right")
    direction.y = Input.get_axis("move_up", "move_down")

    if direction.length() > 0:
        direction = direction.normalized()
        facing = direction

    velocity = direction * SPEED
    move_and_slide()

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_pressed("attack"):
        attack()

func attack() -> void:
    # Attack logic here
    pass

func take_damage(amount: int) -> void:
    health -= amount
    health_changed.emit(health)
    if health <= 0:
        die()

func die() -> void:
    is_dead = true
    player_died.emit()
    velocity = Vector2.ZERO
    set_physics_process(false)
```

---

## Step 3: Camera System

### Create camera.gd

```gdscript
extends Camera2D

@export var target_path: NodePath
@export var smoothing: float = 5.0

var target: Node2D

func _ready() -> void:
    if target_path:
        target = get_node(target_path)
    make_current()

func _physics_process(delta: float) -> void:
    if target:
        position = position.lerp(target.position, smoothing * delta)
```

---

## Step 4: Enemies

### Create enemy.gd

```gdscript
extends CharacterBody2D

enum State { IDLE, CHASE, ATTACK, HURT, DEAD }

const SPEED = 150.0
const CHASE_RANGE = 200.0
const ATTACK_RANGE = 32.0

var health: int = 3
var state: State = State.IDLE
var target: Node2D

@onready var navigation_agent: NavigationAgent2D = $NavigationAgent2D

signal enemy_died(points: int)

func _physics_process(delta: float) -> void:
    match state:
        State.IDLE:
            idle_state(delta)
        State.CHASE:
            chase_state(delta)
        State.ATTACK:
            attack_state(delta)
        State.HURT:
            hurt_state(delta)
        State.DEAD:
            pass

func idle_state(_delta: float) -> void:
    velocity = Vector2.ZERO
    if target and global_position.distance_to(target.global_position) < CHASE_RANGE:
        state = State.CHASE

func chase_state(delta: float) -> void:
    if not target:
        state = State.IDLE
        return

    var direction = global_position.direction_to(target.global_position)
    velocity = direction * SPEED
    move_and_slide()

    if global_position.distance_to(target.global_position) < ATTACK_RANGE:
        state = State.ATTACK

func attack_state(_delta: float) -> void:
    # Attack logic
    if target and target.has_method("take_damage"):
        target.take_damage(1)
    state = State.CHASE

func hurt_state(_delta: float) -> void:
    # Flash red, knockback, etc.
    pass

func take_damage(amount: int) -> void:
    health -= amount
    if health <= 0:
        die()
    else:
        state = State.HURT

func die() -> void:
    state = State.DEAD
    enemy_died.emit(100)
    queue_free()
```

---

## Step 5: Combat System

### Create sword.gd

```gdscript
extends Area2D

@export var damage: int = 1
var is_active: bool = false

func attack() -> void:
    is_active = true
    # Enable collision, play animation
    await get_tree().create_timer(0.2).timeout
    is_active = false

func _on_body_entered(body: Node2D) -> void:
    if is_active and body.has_method("take_damage"):
        body.take_damage(damage)
```

---

## Step 6: Level Design

### Create level.gd

```gdscript
extends Node2D

@onready var player: CharacterBody2D = $Player
@onready var camera: Camera2D = $Camera2D

func _ready() -> void:
    camera.target = player
```

### Use TileMap for walls

1. Create a TileMap node
2. Add a TileSet with wall tiles
3. Paint walls in the editor
4. Set collision polygons on wall tiles

---

## Gotchas

1. **No gravity**: Top-down games don't use gravity — set `velocity.y` directly
2. **Normalization**: Always normalize diagonal movement to prevent faster diagonal speed
3. **Navigation**: Use NavigationAgent2D for enemy pathfinding
4. **Collision layers**: Separate player, enemies, walls, and projectiles
5. **Delta**: Even without gravity, use delta for smooth movement

---

## Cross-References

- [Add AI Guide](add-ai.md) — Enhance enemy behavior
- [Add Collisions Guide](add-collisions.md) — Advanced collision setup
- [Physics Reference](../reference/physics-collision.md) — Physics bodies
- [Script Patterns](../patterns/scripts.md) — Common patterns
