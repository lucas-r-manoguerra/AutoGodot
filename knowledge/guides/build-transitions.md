---
title: "Build Transitions"
type: guide
category: ui
difficulty: intermediate
estimated_time: "30-60 minutes"
prerequisites: ["build-main-menu.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Build Transitions

How to create scene transition effects.

## Overview

**What you'll build:**
- Fade to black
- Slide transitions
- Custom transition effects

---

## Fade Transition

### Create fade_transition.gd

```gdscript
extends CanvasLayer

@onready var color_rect: ColorRect = $ColorRect

var is_transitioning: bool = false

func fade_to_scene(scene_path: String, duration: float = 0.5) -> void:
    if is_transitioning:
        return
    is_transitioning = true

    # Fade out
    var tween = create_tween()
    tween.tween_property(color_rect, "color:a", 1.0, duration / 2.0)
    await tween.finished

    # Change scene
    get_tree().change_scene_to_file(scene_path)

    # Fade in
    tween = create_tween()
    tween.tween_property(color_rect, "color:a", 0.0, duration / 2.0)
    await tween.finished

    is_transitioning = false
```

---

## Slide Transition

### Create slide_transition.gd

```gdscript
extends CanvasLayer

@onready var panel_left: Panel = $PanelLeft
@onready var panel_right: Panel = $PanelRight

func slide_to_scene(scene_path: String) -> void:
    var tween = create_tween().set_parallel(true)

    # Slide panels in
    tween.tween_property(panel_left, "position:x", 0.0, 0.3)
    tween.tween_property(panel_right, "position:x", 0.0, 0.3)
    await tween.finished

    get_tree().change_scene_to_file(scene_path)

    # Reset positions
    panel_left.position.x = -panel_left.size.x
    panel_right.position.x = panel_right.size.x

    # Slide panels out
    tween = create_tween().set_parallel(true)
    tween.tween_property(panel_left, "position:x", -panel_left.size.x, 0.3)
    tween.tween_property(panel_right, "position:x", panel_right.size.x, 0.3)
```

---

## Custom Effects

### Create circle_wipe.gd

```gdscript
extends CanvasLayer

@onready var shader_rect: ColorRect = $ShaderRect

func circle_wipe(scene_path: String) -> void:
    var material = shader_rect.material as ShaderMaterial
    var tween = create_tween()

    # Wipe in (circle shrinks)
    tween.tween_method(func(v): material.set_shader_parameter("radius", v), 1.0, 0.0, 0.5)
    await tween.finished

    get_tree().change_scene_to_file(scene_path)

    # Wipe out (circle grows)
    tween = create_tween()
    tween.tween_method(func(v): material.set_shader_parameter("radius", v), 0.0, 1.0, 0.5)
```

---

## Gotchas

1. **is_transitioning flag**: Prevent double transitions
2. **process_mode**: Set ALWAYS to work during pause
3. **Shader transitions**: Need shader material setup
4. **Audio**: Fade audio alongside visual transitions

---

## Cross-References

- [Build Main Menu](build-main-menu.md) — Menu navigation
- [UI Patterns](../patterns/ui.md) — UI best practices
