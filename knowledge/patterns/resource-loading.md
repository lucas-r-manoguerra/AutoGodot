---
type: Reference
title: Resource Loading
description: preload vs load, PackedScene, .tres resources, and caching behavior in Godot 4.x
tags:
  - resources
  - preload
  - load
  - packed-scene
  - tres
  - caching
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-24T15:00:00Z"
---

# Resource Loading

How Godot loads, caches, and manages resources at runtime.

## preload vs load

| Method | When | Returns | Use When |
|--------|------|---------|----------|
| `preload("res://...")` | Compile time | Cached resource | Scene/resource known at write time |
| `load("res://...")` | Runtime | Resource | Path determined dynamically |

```gdscript
# preload — cached at script load time, fails fast if missing
const ENEMY_SCENE = preload("res://scenes/enemy.tscn")

# load — evaluated at runtime, returns null if missing
func load_level(path: String) -> void:
    var scene = load(path)
    if scene == null:
        push_error("Failed to load: " + path)
        return
    add_child(scene.instantiate())
```

---

## PackedScene Pattern

Scenes are resources. Load them, instantiate them, add them to the tree.

```gdscript
# 1. Load the scene (preload or load)
var enemy_scene = preload("res://scenes/enemy.tscn")

# 2. Instantiate — creates a new node tree from the scene
var enemy = enemy_scene.instantiate()

# 3. Configure before adding
enemy.global_position = Vector2(100, 200)

# 4. Add to the tree
add_child(enemy)
```

### Export PackedScene (editor-configurable)

```gdscript
@export var bullet_scene: PackedScene

func shoot() -> void:
    if bullet_scene == null:
        return
    var bullet = bullet_scene.instantiate()
    bullet.global_position = muzzle.global_position
    get_parent().add_child(bullet)
```

Set the scene in the Inspector — no hardcoded paths.

---

## Resource Types

| Type | Extension | Use For |
|------|-----------|---------|
| `PackedScene` | `.tscn` | Scenes, level layouts |
| `Script` | `.gd` | Game logic |
| `Texture2D` | `.png`, `.jpg` | Sprites, images |
| `AudioStream` | `.wav`, `.ogg` | Sound effects, music |
| `Theme` | `.tres` | UI styling |
| `StyleBox` | `.tres` | Panel/button appearance |
| `FontFile` | `.ttf`, `.otf` | Custom fonts |

---

## .tres Resource Files

External resource files for reusable data:

```
# enemy_data.tres
[gd_resource type="Resource" format=3]

[resource]
script = ExtResource("1")
health = 50
speed = 150.0
damage = 10
```

Load and use:
```gdscript
@export var enemy_data: Resource  # assign .tres in Inspector

func _ready():
    if enemy_data:
        max_health = enemy_data.health
```

---

## Caching Behavior

Godot **caches** resources loaded with `load()` or `preload()`. The second `load()` call returns the same object:

```gdscript
var a = load("res://sprite.png")
var b = load("res://sprite.png")
print(a == b)  # true — same cached resource
```

To force a fresh copy:
```gdscript
var fresh = load("res://sprite.png").duplicate()
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `preload` with dynamic path | Crash — preload needs literal string | Use `load()` for dynamic paths |
| No null check after `load()` | Crash on missing file | Always null-check `load()` results |
| Hardcoding paths in scripts | Breaks when reorganizing folders | Use `@export var scene: PackedScene` |
| Forgetting `.instantiate()` | Node not created | `preload()` returns PackedScene, call `.instantiate()` |
| Loading huge textures at startup | Long load time | Use `load()` on demand, or lazy loading |

---

## Related

- [scene/structures.md](../scene/structures.md) - .tscn file anatomy and ext_resource patterns
- [reference/node-paths.md](../reference/node-paths.md) - Node referencing with $ and get_node()
