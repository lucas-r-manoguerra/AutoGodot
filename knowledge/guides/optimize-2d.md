---
title: "Optimize 2D Performance"
type: guide
category: optimization
difficulty: intermediate
estimated_time: "30-60 minutes"
prerequisites: []
version: "4.7"
created: "2026-07-24"
status: active
---

# Optimize 2D Performance

How to improve 2D game performance in Godot 4.7.

## Overview

**What you'll learn:**
- Object pooling
- Visibility-based activation
- Batch rendering
- Memory management

---

## Object Pooling

### Create object_pool.gd

```gdscript
extends Node

var pool: Array[Node] = []
var scene: PackedScene
var pool_size: int = 50

func _ready(packed_scene: PackedScene, size: int = 50) -> void:
    scene = packed_scene
    pool_size = size

    for i in range(pool_size):
        var obj = scene.instantiate()
        obj.visible = false
        obj.process_mode = Node.PROCESS_MODE_DISABLED
        add_child(obj)
        pool.append(obj)

func get_object() -> Node:
    for obj in pool:
        if not obj.visible:
            obj.visible = true
            obj.process_mode = Node.PROCESS_MODE_INHERIT
            return obj

    # Pool exhausted — create new
    var obj = scene.instantiate()
    add_child(obj)
    pool.append(obj)
    return obj

func return_object(obj: Node) -> void:
    obj.visible = false
    obj.process_mode = Node.PROCESS_MODE_DISABLED
```

---

## Visibility Activation

### Create visible_on_screen.gd

```gdscript
extends VisibleOnScreenNotifier2D

@export var target_node: Node2D

func _on_screen_entered() -> void:
    if target_node:
        target_node.process_mode = Node.PROCESS_MODE_INHERIT

func _on_screen_exited() -> void:
    if target_node:
        target_node.process_mode = Node.PROCESS_MODE_DISABLED
```

---

## Batch Sprites

### Use MultiMeshInstance2D

```gdscript
extends MultiMeshInstance2D

func setup_instances(positions: Array[Vector2], texture: Texture2D) -> void:
    multimesh = MultiMesh.new()
    multimesh.instance_count = positions.size()
    multimesh.mesh = QuadMesh.new()
    multimesh.mesh.size = Vector2(32, 32)
    multimesh.texture = texture

    for i in range(positions.size()):
        multimesh.set_instance_transform_2d(i, Transform2D(0, positions[i]))
```

---

## Tilemap Optimization

```
- Use MultiMeshInstance2D for large tilemaps
- Disable unused layers
- Cull off-screen chunks
- Use visibility_rect for chunks
```

---

## Gotchas

1. **Object pools**: Pre-instantiate, don't create at runtime
2. **VisibilityNotifier**: Disable off-screen nodes
3. **MultiMesh**: Batch similar sprites
4. **Draw calls**: Minimize by batching materials
5. **Physics**: Disable physics for off-screen enemies

---

## Cross-References

- [Optimize Memory](optimize-memory.md) — Memory management
- [Profile Performance](profile-performance.md) — Profiling tools
- [Add Physics](add-physics.md) — Physics optimization
