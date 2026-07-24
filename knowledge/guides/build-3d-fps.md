---
title: "Build a 3D FPS"
type: guide
category: build
difficulty: intermediate
estimated_time: "3-4 hours"
prerequisites: []
version: "4.7"
created: "2026-07-24"
status: active
---

# Build a 3D FPS

Step-by-step guide to creating a first-person shooter in Godot 4.7.

## Overview

**What you'll build:**
- First-person character controller
- Camera with mouse look
- Basic weapon system
- Enemy with simple AI
- Health and ammo HUD
- Level with lighting

---

## Step 1: Project Setup

### Create project.godot

```ini
config_version=5

[application]

config/name="3D FPS"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")

[display]

window/size/viewport_width=1920
window/size/viewport_height=1080

[input]

move_forward={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":87,"key_label":0,"unicode":119,"location":0,"echo":false,"script":null)
]
}
move_backward={
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
jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"location":0,"echo":false,"script":null)
]
}
shoot={
"deadzone": 0.5,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"button_mask":1,"position":Vector2(0,0),"global_position":Vector2(0,0),"factor":1.0,"button_index":1,"canceled":false,"pressed":false,"double_click":false,"script":null)
]
}

[rendering]

renderer/rendering_method="forward_plus"
```

---

## Step 2: Player Controller

### Create player.gd

```gdscript
extends CharacterBody3D

const SPEED = 5.0
const JUMP_VELOCITY = 4.5
const MOUSE_SENSITIVITY = 0.002

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var health: int = 100

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var raycast: RayCast3D = $Head/Camera3D/RayCast3D

signal health_changed(new_health: int)
signal player_died

func _ready() -> void:
    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
    capture_mouse()

func _unhandled_input(event: InputEvent) -> void:
    # Mouse look
    if event is InputEventMouseMotion:
        rotate_y(-event.relative.x * MOUSE_SENSITIVITY)
        head.rotate_x(-event.relative.y * MOUSE_SENSITIVITY)
        head.rotation.x = clamp(head.rotation.x, -PI/2, PI/2)

    # Release mouse
    if event.is_action_pressed("ui_cancel"):
        Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _physics_process(delta: float) -> void:
    # Gravity
    if not is_on_floor():
        velocity.y -= gravity * delta

    # Jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    # Movement
    var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
    var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()

    if direction:
        velocity.x = direction.x * SPEED
        velocity.z = direction.z * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        velocity.z = move_toward(velocity.z, 0, SPEED)

    move_and_slide()

func capture_mouse() -> void:
    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func take_damage(amount: int) -> void:
    health -= amount
    health_changed.emit(health)
    if health <= 0:
        die()

func die() -> void:
    player_died.emit()
    Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
```

---

## Step 3: Weapon System

### Create weapon.gd

```gdscript
extends Node3D

@export var damage: int = 25
@export var range: float = 100.0
@export var fire_rate: float = 0.1

var can_fire: bool = true

@onready var raycast: RayCast3D = $RayCast3D
@onready var muzzle_flash: GPUParticles3D = $MuzzleFlash

func _ready() -> void:
    raycast.target_position = Vector3(0, 0, -range)

func _process(_delta: float) -> void:
    if Input.is_action_pressed("shoot") and can_fire:
        fire()

func fire() -> void:
    can_fire = false
    muzzle_flash.restart()

    if raycast.is_colliding():
        var body = raycast.get_collider()
        if body.has_method("take_damage"):
            body.take_damage(damage)

    await get_tree().create_timer(fire_rate).timeout
    can_fire = true
```

---

## Step 4: Enemies

### Create enemy.gd

```gdscript
extends CharacterBody3D

enum State { IDLE, CHASE, ATTACK, DEAD }

const SPEED = 3.0
const CHASE_RANGE = 20.0
const ATTACK_RANGE = 2.0

var health: int = 50
var state: State = State.IDLE
var target: Node3D

@onready var navigation_agent: NavigationAgent3D = $NavigationAgent3D

signal enemy_died(points: int)

func _physics_process(delta: float) -> void:
    match state:
        State.IDLE:
            idle_state(delta)
        State.CHASE:
            chase_state(delta)
        State.ATTACK:
            attack_state(delta)
        State.DEAD:
            pass

    # Gravity
    if not is_on_floor():
        velocity.y -= ProjectSettings.get_setting("physics/3d/default_gravity") * delta

    move_and_slide()

func idle_state(_delta: float) -> void:
    velocity = Vector3.ZERO
    if target and global_position.distance_to(target.global_position) < CHASE_RANGE:
        state = State.CHASE

func chase_state(_delta: float) -> void:
    if not target:
        state = State.IDLE
        return

    navigation_agent.target_position = target.global_position
    if navigation_agent.is_navigation_finished():
        return

    var next_position = navigation_agent.get_next_path_position()
    var direction = global_position.direction_to(next_position)
    velocity = direction * SPEED

    if global_position.distance_to(target.global_position) < ATTACK_RANGE:
        state = State.ATTACK

func attack_state(_delta: float) -> void:
    if target and target.has_method("take_damage"):
        target.take_damage(10)
    state = State.CHASE

func take_damage(amount: int) -> void:
    health -= amount
    if health <= 0:
        die()

func die() -> void:
    state = State.DEAD
    enemy_died.emit(100)
    queue_free()
```

---

## Step 5: HUD

### Create hud.gd

```gdscript
extends CanvasLayer

@onready var health_label: Label = $HealthLabel
@onready var crosshair: TextureRect = $Crosshair

func update_health(health: int) -> void:
    health_label.text = "Health: %d" % health
```

---

## Step 6: Level

### Create level.tscn

1. Add WorldEnvironment with sky
2. Add DirectionalLight3D for sun
3. Add Player instance
4. Add NavigationRegion3D with ground mesh
5. Add enemy instances
6. Add MeshInstance3D walls/obstacles

---

## Gotchas

1. **Mouse capture**: Call `Input.mouse_mode = Input.MOUSE_MODE_CAPTURED` in `_ready()`
2. **Forward+ renderer**: Required for 3D features like glow, SDFGI
3. **Navigation**: Use NavigationAgent3D for enemy pathfinding
4. **Collision layers**: Player=1, Enemies=2, Projectiles=3, Environment=4
5. **RayCast for weapons**: More reliable than physics bodies for hitscan

---

## Cross-References

- [Add AI Guide](add-ai.md) — Enhance enemy behavior
- [Add Collisions Guide](add-collisions.md) — Advanced collision setup
- [Physics Reference](../reference/physics-collision.md) — Physics bodies
- [Migration Guide](../migration/godot-4.md) — Godot 4.x changes
