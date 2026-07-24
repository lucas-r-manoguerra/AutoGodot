---
type: MigrationGuide
title: "Godot 3.x to 4.x Migration Reference"
description: Quick-reference for the API changes that trip up AI agents most often, all code examples use Godot 4.7 syntax exclusively
tags:
  - migration
  - godot-4
  - api-changes
  - move-and-slide
  - signals
  - await
  - physics-server
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-24T15:00:00Z"
---

# Godot 3.x → 4.x Migration Reference

Quick-reference for the API changes that trip up AI agents most often.
All code examples use **Godot 4.7** syntax exclusively.

---

## Movement — move_and_slide

`move_and_slide()` no longer takes velocity as an argument. Velocity is now a
built-in property on `CharacterBody2D`.

| | Old (3.x) | New (4.x) |
|---|-----------|-----------|
| **Call** | `move_and_slide(velocity)` | `self.velocity = velocity` then `move_and_slide()` |

```gdscript
# ✗ OLD
velocity = direction * speed
move_and_slide(velocity)

# ✓ NEW
velocity = direction * speed
move_and_slide()
```

> See also: [patterns/scripts.md](../patterns/scripts.md) for complete movement patterns including top-down and platformer examples.

---

## Signal Connection

Signal syntax moved from string-based to type-safe callable references.

| | Old (3.x) | New (4.x) |
|---|-----------|-----------|
| **Connect** | `signal_name.connect(obj, "method")` | `signal_name.connect(method)` |
| **Emit** | `emit_signal("signal_name", args)` | `signal_name.emit(args)` |

```gdscript
# ✗ OLD
enemy.connect("enemy_died", self, "_on_enemy_died")
emit_signal("health_changed", health)

# ✓ NEW
enemy.enemy_died.connect(_on_enemy_died)
health_changed.emit(health)
```

---

## Exports and Onready

Annotations replace keywords. The `@` prefix is required.

| | Old (3.x) | New (4.x) |
|---|-----------|-----------|
| **Export** | `export var speed: float = 300.0` | `@export var speed: float = 300.0` |
| **Onready** | `onready var label = $Label` | `@onready var label = $Label` |

```gdscript
# ✗ OLD
export var speed: float = 300.0
onready var score_label = $ScoreLabel

# ✓ NEW
@export var speed: float = 300.0
@onready var score_label = $ScoreLabel
```

---

## yield → await

Coroutines use `await` instead of `yield`.

| | Old (3.x) | New (4.x) |
|---|-----------|-----------|
| **Wait** | `yield(get_tree().create_timer(1.0), "timeout")` | `await get_tree().create_timer(1.0).timeout` |
| **Signal** | `yield(obj, "signal_name")` | `await signal_name` |

```gdscript
# ✗ OLD
yield(get_tree().create_timer(2.0), "timeout")
queue_free()

# ✓ NEW
await get_tree().create_timer(2.0).timeout
queue_free()
```

---

## Physics Server Rename

The physics singletons were reordered to follow a consistent naming convention.

| | Old (3.x) | New (4.x) |
|---|-----------|-----------|
| **2D** | `Physics2DServer` | `PhysicsServer2D` |
| **3D** | `PhysicsServer` | `PhysicsServer3D` |

```gdscript
# ✗ OLD
Physics2DServer.area_get_shape(...)

# ✓ NEW
PhysicsServer2D.area_get_shape(...)
```

---

## Scene Change

`change_scene()` was renamed for clarity and now requires a file path.

| | Old (3.x) | New (4.x) |
|---|-----------|-----------|
| **By path** | `get_tree().change_scene("res://scene.tscn")` | `get_tree().change_scene_to_file("res://scene.tscn")` |
| **By PackedScene** | *(not available)* | `get_tree().change_scene_to_packed(scene)` |

```gdscript
# ✗ OLD
get_tree().change_scene("res://scenes/game_over.tscn")

# ✓ NEW
get_tree().change_scene_to_file("res://scenes/game_over.tscn")
```

> See also: [patterns/ui.md](../patterns/ui.md) for menu screen scene changes using `change_scene_to_file`.

---

## Collision Layers

The underlying bitmask model is the same, but the Inspector labels changed
and the setter API is more explicit. Values are bitmasks where each bit
represents a layer.

| | Old (3.x) | New (4.x) |
|---|-----------|-----------|
| **Layer** | `collision_layer = 1` (bitmask int) | `collision_layer = 1` (same bitmask int) |
| **Mask** | `collision_mask = 1` (bitmask int) | `collision_mask = 1` (same bitmask int) |

```gdscript
# Layer 1 bit set = 1, Layer 2 bit set = 2, Layers 1+2 = 3
func _ready():
    collision_layer = 1   # This node is on layer 1
    collision_mask = 3    # Collides with layers 1 and 2
```

> The values didn't change, but agents often forget that these are **bitmasks**,
> not sequential layer numbers. Use `1`, `2`, `4`, `8` for individual layers.

---

## _process and _physics_process

Function signatures are unchanged. The key difference is that `_ready()`,
`_process()`, and `_physics_process()` are called automatically — do not
connect them manually.

```gdscript
# This is identical in 3.x and 4.x:
func _ready():
    print("Node is ready")

func _process(delta: float):
    # Per-frame logic
    pass

func _physics_process(delta: float):
    # Fixed-step physics logic
    pass
```

> If you need a tool script, prefix with `@tool` at the top of the file.

---

## Quick Conversion Checklist

Before returning any Godot 4.x code, verify:

- [ ] `move_and_slide()` has no arguments
- [ ] `signal.connect(callable)` uses no strings
- [ ] `signal.emit()` replaces `emit_signal()`
- [ ] `@export` and `@onready` have the `@` prefix
- [ ] `await` replaces `yield`
- [ ] `PhysicsServer2D` replaces `Physics2DServer`
- [ ] `change_scene_to_file()` replaces `change_scene()`
- [ ] `change_scene_to_packed()` is used when passing a PackedScene
- [ ] Collision values are bitmasks (`1`, `2`, `4`, `8`), not layer indices
