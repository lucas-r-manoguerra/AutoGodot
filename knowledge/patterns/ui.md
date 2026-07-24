---
type: Reference
title: UI Patterns
description: CanvasLayer setup, HUD layout, menus, health bars, and responsive UI for Godot 4.x
tags:
  - ui
  - canvas-layer
  - hud
  - menus
  - labels
  - health-bar
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-24T15:00:00Z"
---

# UI Patterns

Godot UI renders inside `CanvasLayer` nodes so it stays on top of the game world.

## CanvasLayer Setup

Every HUD or menu needs a `CanvasLayer` as root — otherwise UI moves with the camera.

```
CanvasLayer          ← renders on top of game
├── MarginContainer  ← optional padding
│   ├── ScoreLabel
│   └── HealthLabel
└── ColorRect        ← background overlay
```

---

## HUD Layout

Position labels with `offset_*` properties. These are absolute pixel positions from the parent's top-left.

```gdscript
# game_ui.gd — update labels from signals
extends CanvasLayer

@onready var score_label: Label = $ScoreLabel
@onready var health_label: Label = $HealthLabel

func _on_score_changed(new_score: int) -> void:
    score_label.text = "Score: %d" % new_score

func _on_health_changed(new_health: int) -> void:
    health_label.text = "Health: %d" % new_health
```

### Label Positioning (offset values)

| Position | offset_left | offset_top | offset_right | offset_bottom |
|----------|------------|------------|--------------|---------------|
| Top-left | 20.0 | 20.0 | 250.0 | 50.0 |
| Top-right | anchor_right=1.0, offset_left=-230 | 20.0 | -20.0 | 50.0 |
| Center | anchor_left=0.5, anchor_right=0.5, offset_left=-100 | anchor_top=0.5, offset_top=-15 | 100.0 | 15.0 |

---

## ColorRect Background

Use `ColorRect` for solid-color backgrounds. Must be sized manually (or anchored to fill).

```
[Offset]
ColorRect
├── anchor_right = 1.0
├── anchor_bottom = 1.0
├── color = Color(0.15, 0.15, 0.2, 1)
```

Dark background colors that work well:
- Space/dark: `Color(0.15, 0.15, 0.2, 1)`
- Forest: `Color(0.1, 0.2, 0.1, 1)`
- Desert: `Color(0.3, 0.25, 0.15, 1)`

---

## Menu Screen Pattern

```
CanvasLayer
├── TitleLabel     (center, large font)
├── StartButton    (center-below)
└── Background     (ColorRect, full screen)
```

```gdscript
# menu.gd
extends CanvasLayer

@onready var start_button: Button = $StartButton

func _ready() -> void:
    start_button.pressed.connect(_on_start_pressed)

func _on_start_pressed() -> void:
    get_tree().change_scene_to_file("res://scenes/main.tscn")
```

---

## Health Bar Pattern

Use `TextureProgressBar` or a label-based approach:

```gdscript
# Label-based health display
func _on_health_changed(new_health: int) -> void:
    health_label.text = "Health: %d" % new_health
    if new_health <= 25:
        health_label.add_theme_color_override("font_color", Color.RED)
    elif new_health <= 50:
        health_label.add_theme_color_override("font_color", Color.YELLOW)
    else:
        health_label.add_theme_color_override("font_color", Color.WHITE)
```

---

## Common UI Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| No CanvasLayer | UI scrolls with camera | Wrap UI in CanvasLayer |
| Labels use position instead of offset | Anchor system breaks | Use offset_left/top/right/bottom |
| UI drawn before game | Z-order wrong | CanvasLayer renders on top by default |
| No theme override for color | White text on white bg | Add `theme_override_colors/font_color` |

---

## Related

- [checklists/character-scene.md](../checklists/character-scene.md) - Required nodes for character scenes
- [reference/exported-vars.md](../reference/exported-vars.md) - @export and @onready patterns
- [reference/node-paths.md](../reference/node-paths.md) - Node referencing with $ and get_node()
