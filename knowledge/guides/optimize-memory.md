---
title: "Optimize Memory Usage"
type: guide
category: optimization
difficulty: intermediate
estimated_time: "30-60 minutes"
prerequisites: []
version: "4.7"
created: "2026-07-24"
status: active
---

# Optimize Memory Usage

How to reduce memory consumption in Godot 4.7.

## Overview

**What you'll learn:**
- Resource preloading
- Texture compression
- Scene instancing
- Garbage collection

---

## Resource Preloading

### Create resource_cache.gd

```gdscript
extends Node

var cache: Dictionary = {}

func preload_resource(path: String) -> Resource:
    if not cache.has(path):
        cache[path] = load(path)
    return cache[path]

func clear_cache() -> void:
    cache.clear()
```

### Use preload() for static resources

```gdscript
# Good — loads at parse time
const HEALTH_PACK = preload("res://resources/health_pack.tscn")

# Bad — loads at runtime
func spawn_health():
    var pack = load("res://resources/health_pack.tscn")
```

---

## Texture Compression

### In Godot Editor

```
Project > Project Settings > Rendering > Textures >
  - VRAM Compression: Enable for mobile/desktop
  - Default Compression Mode: VRAM Compressed
  - Max Texture Size: 2048 (reduce if possible)
```

### Import settings

```
Select texture > Inspector > Import:
  - Compression Mode: VRAM Compressed
  - Mipmaps: Generate (for 3D)
  - Roughness: Detect (for PBR)
```

---

## Scene Instancing

### Use PackedScene.instantiate()

```gdscript
# Bad — creates new resource every time
var enemy = load("res://scenes/enemy.tscn").instantiate()

# Good — reuse packed scene
const ENEMY_SCENE = preload("res://scenes/enemy.tscn")

func spawn_enemy():
    var enemy = ENEMY_SCENE.instantiate()
    add_child(enemy)
```

---

## Memory Monitoring

### Create memory_monitor.gd

```gdscript
extends Label

func _process(_delta: float) -> void:
    var static_mem = OS.get_static_memory_usage() / 1024 / 1024
    var video_mem = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1024 / 1024
    text = "RAM: %.1f MB | VRAM: %.1f MB" % [static_mem, video_mem]
```

---

## Gotchas

1. **preload vs load**: preload is faster, load is for dynamic
2. **Texture size**: Reduce for mobile games
3. **Audio**: Use OGG for music, WAV for SFX
4. **Instances**: Reuse nodes via pool, don't create/destroy
5. **Signals**: Disconnect when node is freed

---

## Cross-References

- [Optimize 2D](optimize-2d.md) — Object pooling
- [Profile Performance](profile-performance.md) — Profiling tools
- [Scale Project](scale-project.md) — Scaling strategies
