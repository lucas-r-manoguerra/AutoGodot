---
title: "Profile Performance"
type: guide
category: optimization
difficulty: intermediate
estimated_time: "30-60 minutes"
prerequisites: []
version: "4.7"
created: "2026-07-24"
status: active
---

# Profile Performance

How to identify and fix performance bottlenecks.

## Overview

**What you'll learn:**
- Using Godot's profiler
- FPS monitoring
- Draw call optimization
- Common bottlenecks

---

## Built-in Profiler

### Open profiler

```
Debugger > Profiler
```

### Key metrics

```
- Frame time: Should be < 16.67ms for 60 FPS
- Physics: Should be < 8ms
- Process: Game logic time
- Render: Drawing time
- Physics objects: Number of active bodies
- Nodes: Total active nodes
```

---

## FPS Monitor

### Create fps_monitor.gd

```gdscript
extends Label

func _process(_delta: float) -> void:
    text = "FPS: %d" % Engine.get_frames_per_second()
    if Engine.get_frames_per_second() < 30:
        add_theme_color_override("font_color", Color.RED)
    else:
        add_theme_color_override("font_color", Color.GREEN)
```

---

## Draw Call Monitor

### Create draw_call_monitor.gd

```gdscript
extends Label

func _process(_delta: float) -> void:
    var draw_calls = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
    text = "Draw Calls: %d" % draw_calls
```

---

## Common Bottlenecks

### 1. Too many nodes

```
Problem: 1000+ active nodes
Solution: Object pooling, visibility deactivation
```

### 2. Physics overload

```
Problem: Too many collision checks
Solution: Simplify collision shapes, reduce layers
```

### 3. Script processing

```
Problem: _process() doing too much
Solution: Cache values, reduce frequency
```

### 4. Draw calls

```
Problem: Too many sprites/materials
Solution: Batch with MultiMesh, use texture atlases
```

---

## Optimization Checklist

```
□ FPS stable at target (30/60)
□ Draw calls < 100
□ Physics bodies < 100
□ Node count reasonable
□ No memory leaks
□ Texture sizes optimized
□ Audio compression enabled
```

---

## Gotchas

1. **Profiler overhead**: Don't profile in release builds
2. **Mobile vs Desktop**: Profile on target platform
3. **GDScript vs C#**: GDScript is slower for heavy computation
4. **Shaders**: Complex shaders impact GPU

---

## Cross-References

- [Optimize 2D](optimize-2d.md) — Object pooling
- [Optimize Memory](optimize-memory.md) — Memory management
- [Scale Project](scale-project.md) — Scaling strategies
