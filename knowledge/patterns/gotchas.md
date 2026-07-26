---
type: Reference
title: Godot 4.x Gotchas
description: Common pitfalls and anti-patterns discovered through real debugging sessions with AI-generated code
tags:
  - godot
  - gotchas
  - debugging
  - ai-generated
  - rendering
  - indentation
  - api
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-25T00:00:00Z"
---

# Godot 4.x Gotchas

Common pitfalls discovered through real debugging sessions. These are the patterns that cause the most pain when AI generates code for Godot.

## 1. Rendering: Control Node Covers Parent _draw()

**Symptom:** `_draw()` calls produce nothing visible. The game shows only text labels, no shapes or colors.

**Root cause:** A `ColorRect`, `Label`, or any `Control` node placed as a **child** of `Node2D` renders ON TOP of the parent's `_draw()`. Godot's rendering pipeline draws children after the parent, and Control nodes fill their entire area with a solid background.

**Fix:**
```gdscript
# BAD — ColorRect covers Node2D._draw()
# Node2D (has _draw()) -> ColorRect

# GOOD — Use CanvasLayer for UI overlays
# Node2D (has _draw()) -> CanvasLayer -> ColorRect

# GOOD — Draw backgrounds in _draw() directly
func _draw():
    draw_rect(Rect2(0, 0, 1024, 600), Color.BLACK)
```

**Detection:** `gdcheck` and `create_scene` both warn about this hierarchy.

---

## 2. Indentation: Mixed Tabs and Spaces

**Symptom:** `Parse Error` with no clear indication of which line is wrong.

**Root cause:** Godot 4.x GDScript **rejects** files with mixed indentation. Even a single tab in a spaces-only file causes parse errors. LLMs sometimes inject tab characters.

**Fix:**
- Use 4 spaces consistently in all GDScript files
- `write_game_file` now auto-fixes tabs→spaces after writing
- `create_script` validates indentation before creation
- Run `gdcheck` to detect mixed indentation

---

## 3. CLI: class_name Not Indexed

**Symptom:** `Could not find type "MyData"` when running Godot from CLI, even though it works in the editor.

**Root cause:** Godot CLI doesn't index new scripts with `class_name` declarations. The editor indexes them on save, but CLI runs don't trigger this.

**Fix:**
```gdscript
# BAD — class_name not resolved in CLI
class_name MyData
extends RefCounted

# GOOD — preload() works everywhere
# In the script that uses it:
var D = preload("res://scripts/my_data.gd")
```

**Detection:** `gdcheck` warns about `class_name` usage with CLI compatibility info.

---

## 4. Architecture: Monolithic Scripts

**Symptom:** Debugging takes forever. When `_draw()` doesn't render, finding the cause in 300 lines is painful.

**Root cause:** AI tends to generate large, monolithic scripts mixing data, logic, rendering, and UI.

**Fix:** One file = one task.
```
scripts/
  tetris_data.gd      # Constants only
  tetris_board.gd      # Board state management
  tetris_piece.gd      # Piece logic
  tetris_draw.gd       # All rendering functions
  tetris_ui.gd         # Label management
  game.gd              # Thin orchestrator
```

**Detection:** `gdcheck` warns about files over 300 lines.

---

## 5. API: move_and_slide() Signature Changed

**Symptom:** `Expected 0 arguments, got 1` or velocity not applied.

**Root cause:** In Godot 3: `move_and_slide(velocity)`. In Godot 4: `move_and_slide()` takes NO arguments — velocity is a property.

**Fix:**
```gdscript
# BAD — Godot 3 syntax
move_and_slide(direction * speed)

# GOOD — Godot 4 syntax
velocity = direction * speed
move_and_slide()
```

**Detection:** `gdcheck` detects `move_and_slide(args)` pattern.

---

## 6. API: String-Based connect() Deprecated

**Symptom:** Signal connection fails silently in Godot 4.

**Root cause:** `signal.connect('method_name', target)` is Godot 3 syntax.

**Fix:**
```gdscript
# BAD — Godot 3
connect('hit', self, '_on_hit')

# GOOD — Godot 4
hit.connect(_on_hit)
```

**Detection:** `gdcheck` detects `.connect('` pattern.

---

## 7. API: export/onready Are Annotations

**Symptom:** Variables not exposed in inspector, nodes not found.

**Root cause:** `export var` and `onready var` are Godot 3 keywords. Godot 4 uses `@export` and `@onready` annotations.

**Fix:**
```gdscript
# BAD — Godot 3
export var speed = 100
onready var sprite = $Sprite2D

# GOOD — Godot 4
@export var speed: float = 100.0
@onready var sprite = $Sprite2D
```

**Detection:** `gdcheck` detects `export var` and `onready var` patterns.

---

## 8. Scene: CollisionShape Needs Physics Body Parent

**Symptom:** Collisions don't work. No error messages.

**Root cause:** `CollisionShape2D`/`3D` only function under `CharacterBody`, `Area`, `StaticBody`, or `RigidBody` nodes.

**Fix:**
```gdscript
# BAD — CollisionShape under Node2D
# Node2D -> CollisionShape2D

# GOOD — CollisionShape under CharacterBody2D
# CharacterBody2D -> CollisionShape2D
```

**Detection:** `create_scene` warns about this hierarchy.

---

## 9. Scene: 2D and 3D Mixed in Same Branch

**Symptom:** Nodes invisible or rendering glitches.

**Root cause:** Mixing `Node2D` and `Node3D` in the same parent-child branch causes rendering issues.

**Fix:** Keep 2D and 3D in separate scene trees with separate root nodes.

**Detection:** `create_scene` warns about this.

---

## 10. Rendering: CanvasLayer for HUD

**Symptom:** UI elements scroll with the camera.

**Root cause:** UI nodes at the same z-level as game objects move with camera transforms.

**Fix:**
```
Root -> CanvasLayer -> Label (Score), Label (Health)
```

The `CanvasLayer` renders on a separate canvas layer that doesn't transform with the camera.

---

## 11. Scene: unique_name_in_owner for %NodeName

**Symptom:** `%NodeName` returns null in `@onready`.

**Root cause:** Using `%NodeName` requires the node to have `unique_name_in_owner = true` in the `.tscn` file.

**Fix:** Set `unique_name_in_owner = true` on the node in the scene file, or use `$path` instead.

---

## 12. Performance: queue_redraw() in _process()

**Symptom:** High CPU usage, `_draw()` called 60 times/sec.

**Root cause:** Calling `queue_redraw()` every frame forces constant redraws.

**Fix:** Only call `queue_redraw()` when state changes. For static content, `_draw()` is called once automatically.

---

## 13. Debugging: Engine Errors vs Script Errors

**Symptom:** Console full of scary-looking errors that aren't actually problems.

**Root cause:** Godot outputs many engine-level errors (`BUG: Unreferenced static string`, `RID leaks`) during cleanup that are NOT script errors.

**Fix:** Filter for `SCRIPT ERROR` or your script filename specifically. Engine cleanup messages at exit are normal.

---

## 14. Rendering: Unique Names in Scene

**Symptom:** Node not found when using `$NodeName` or `%NodeName`.

**Root cause:** Duplicate node names in the same parent, or missing `unique_name_in_owner`.

**Fix:** Ensure unique names within each parent scope. Use `%` prefix only with `unique_name_in_owner = true`.
