---
title: "Scale Project"
type: guide
category: optimization
difficulty: advanced
estimated_time: "1-2 hours"
prerequisites: ["optimize-2d.md", "optimize-memory.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Scale Project

How to structure and scale Godot projects.

## Overview

**What you'll learn:**
- Project folder structure
- Resource management
- Scene organization
- Performance at scale

---

## Recommended Folder Structure

```
project/
├── scenes/
│   ├── main.tscn
│   ├── player/
│   ├── enemies/
│   ├── ui/
│   └── levels/
├── scripts/
│   ├── autoload/
│   ├── player/
│   ├── enemies/
│   └── ui/
├── resources/
│   ├── items/
│   ├── enemies/
│   └── themes/
├── assets/
│   ├── sprites/
│   ├── audio/
│   └── fonts/
└── addons/
```

---

## Autoload Singletons

### Create autoload_manager.gd

```gdscript
extends Node

# Game state
var current_level: String = "level_1"
var player_position: Vector2 = Vector2.ZERO

# Systems
var dialogue_manager: Node
var settings_manager: Node
var save_manager: Node

func _ready() -> void:
    dialogue_manager = get_node("/root/DialogueManager")
    settings_manager = get_node("/root/SettingsManager")
    save_manager = get_node("/root/SaveManager")
```

---

## Scene Management

### Create scene_manager.gd

```gdscript
extends Node

var current_scene: Node
var scene_stack: Array[String] = []

func change_scene(scene_path: String) -> void:
    if current_scene:
        scene_stack.append(current_scene.scene_file_path)
    get_tree().change_scene_to_file(scene_path)
    current_scene = get_tree().current_scene

func go_back() -> void:
    if scene_stack.size() > 0:
        var prev_scene = scene_stack.pop_back()
        get_tree().change_scene_to_file(prev_scene)
```

---

## Resource Management

### Create resource_manager.gd

```gdscript
extends Node

var loaded_resources: Dictionary = {}

func get_resource(path: String) -> Resource:
    if not loaded_resources.has(path):
        loaded_resources[path] = load(path)
    return loaded_resources[path]

func unload_all() -> void:
    loaded_resources.clear()
```

---

## Scalability Tips

```
1. Modular scenes: Each entity is its own scene
2. Signals: Loose coupling between systems
3. Autoloads: Singletons for global state
4. Resource loading: Lazy load heavy resources
5. Object pooling: Reuse nodes
6. Visibility deactivation: Disable off-screen
7. State machines: Organize complex behavior
8. Component pattern: Mix and match capabilities
```

---

## Gotchas

1. **Scene hierarchy**: Keep depth manageable
2. **Signal connections**: Disconnect on free
3. **Resource leaks**: Unload unused resources
4. **Circular dependencies**: Use signals instead
5. **Build size**: Strip unused resources

---

## Cross-References

- [Optimize 2D](optimize-2d.md) — Performance tips
- [Optimize Memory](optimize-memory.md) — Memory management
- [Profile Performance](profile-performance.md) — Profiling tools
- [GDScript Patterns](../patterns/gdscript.md) — Code organization
