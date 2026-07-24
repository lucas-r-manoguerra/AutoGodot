---
title: "Add Physics to Your Game"
type: guide
category: feature
difficulty: beginner
estimated_time: "30-60 minutes"
prerequisites: ["build-2d-platformer.md", "build-2d-topdown.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Add Physics to Your Game

How to add physics bodies, forces, and interactions to your Godot project.

## Overview

**What you'll learn:**
- Physics body types (CharacterBody, RigidBody, StaticBody)
- When to use each type
- Applying forces and impulses
- Gravity and jump mechanics

---

## Physics Body Types

### CharacterBody2D/3D

For player-controlled characters and enemies that need custom movement.

```gdscript
extends CharacterBody2D

const SPEED = 300.0
const JUMP_VELOCITY = -400.0

var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")

func _physics_process(delta: float) -> void:
    # Apply gravity
    if not is_on_floor():
        velocity.y += gravity * delta

    # Jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    # Movement
    var direction := Input.get_axis("move_left", "move_right")
    velocity.x = direction * SPEED

    move_and_slide()
```

**Use when:**
- Player characters
- Enemies with custom AI
- NPCs with dialogue

### RigidBody2D/3D

For objects that respond to physics forces automatically.

```gdscript
extends RigidBody2D

func explode(force: Vector2) -> void:
    apply_central_impulse(force)
    apply_torque_impulse(randf_range(-100, 100))
```

**Use when:**
- Destructible objects
- Projectiles
- Ragdolls
- Physics puzzles

### StaticBody2D/3D

For immovable objects like walls, floors, and platforms.

```gdscript
extends StaticBody2D

# Static bodies don't need scripts usually
# Just add collision shape in editor
```

**Use when:**
- Walls and floors
- Platforms
- Doors (when not moving)
- Triggers (use Area2D instead)

---

## Applying Forces

### CharacterBody (manual movement)

```gdscript
# Direct velocity control
velocity = direction * SPEED

# With acceleration
velocity.x = move_toward(velocity.x, target_speed, acceleration * delta)
```

### RigidBody (physics forces)

```gdscript
# One-time impulse
apply_central_impulse(Vector2(100, -200))

# Continuous force
func _physics_process(delta: float) -> void:
    apply_central_force(Vector2(100, 0) * delta)

# Torque (rotation)
apply_torque_impulse(50.0)
```

---

## Gravity

### Custom gravity

```gdscript
var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y += gravity * delta
```

### Zero gravity (space games)

```gdscript
func _physics_process(delta: float) -> void:
    # No gravity applied
    var direction := Input.get_vector("left", "right", "up", "down")
    velocity = direction * SPEED
    move_and_slide()
```

---

## Jump Mechanics

### Simple jump

```gdscript
const JUMP_VELOCITY = -400.0

func _physics_process(delta: float) -> void:
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY
```

### Variable jump height

```gdscript
const JUMP_VELOCITY = -400.0
const JUMP_CUT_MULTIPLIER = 0.5

func _physics_process(delta: float) -> void:
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    # Cut jump short if button released
    if Input.is_action_just_released("jump") and velocity.y < 0:
        velocity.y *= JUMP_CUT_MULTIPLIER
```

### Coyote time

```gdscript
var coyote_timer: float = 0.0
const COYOTE_TIME = 0.1

func _physics_process(delta: float) -> void:
    # Track time since on floor
    if is_on_floor():
        coyote_timer = COYOTE_TIME
    else:
        coyote_timer -= delta

    # Jump if within coyote time
    if Input.is_action_just_pressed("jump") and coyote_timer > 0:
        velocity.y = JUMP_VELOCITY
        coyote_timer = 0.0
```

---

## Gotchas

1. **Always use delta**: Multiply all physics by `delta` for frame-rate independence
2. **Normalize direction**: Use `.normalized()` for diagonal movement
3. **Check is_on_floor()**: Before allowing jump
4. **Use move_and_slide()**: Handles collision response automatically
5. **Set collision layers**: Separate player, enemies, and environment

---

## Cross-References

- [Add Collisions Guide](add-collisions.md) — Collision layers and signals
- [Physics Reference](../reference/physics-collision.md) — Complete physics docs
- [Script Patterns](../patterns/scripts.md) — Common GDScript patterns
