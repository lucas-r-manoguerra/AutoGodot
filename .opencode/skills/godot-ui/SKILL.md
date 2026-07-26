---
name: godot-ui
description: "Godot UI with Control nodes, CanvasLayer, HUD, menus, theming, and layout. Triggers on: UI, HUD, menu, Control, CanvasLayer, Label, Button, theme."
---

# Godot UI Patterns

CanvasLayer setup, HUD layout, menus, and theming.

## CanvasLayer is MANDATORY for HUD

Without CanvasLayer, UI scrolls with the camera:

```
# BAD — UI moves with camera
Main (Node2D)
├── Player
├── ScoreLabel (Label)  ← scrolls away!

# GOOD — UI stays fixed
Main (Node2D)
├── Player
└── HUD (CanvasLayer)
    └── ScoreLabel (Label)  ← stays on screen
```

## Label Positioning

Labels use `offset_*` properties (not `position`):

| Position | offset_left | offset_top | offset_right | offset_bottom |
|----------|------------|------------|--------------|---------------|
| Top-left | 20.0 | 20.0 | 250.0 | 50.0 |
| Top-right | anchor_right=1.0, offset_left=-230 | 20.0 | -20.0 | 50.0 |
| Center | anchor_left=0.5, anchor_right=0.5, offset_left=-100 | anchor_top=0.5, offset_top=-15 | 100.0 | 15.0 |

## HUD Script Pattern

```gdscript
extends CanvasLayer

@onready var score_label: Label = $ScoreLabel
@onready var health_label: Label = $HealthLabel

func _on_score_changed(new_score: int) -> void:
    score_label.text = "Score: %d" % new_score

func _on_health_changed(new_health: int) -> void:
    health_label.text = "Health: %d" % new_health
    if new_health <= 25:
        health_label.add_theme_color_override("font_color", Color.RED)
    elif new_health <= 50:
        health_label.add_theme_color_override("font_color", Color.YELLOW)
    else:
        health_label.add_theme_color_override("font_color", Color.WHITE)
```

## Menu Screen Pattern

```
CanvasLayer
├── Background (ColorRect, full screen)
├── TitleLabel (center, large font)
└── StartButton (center-below)
```

```gdscript
extends CanvasLayer

@onready var start_button: Button = $StartButton

func _ready() -> void:
    start_button.pressed.connect(_on_start_pressed)

func _on_start_pressed() -> void:
    get_tree().change_scene_to_file("res://scenes/main.tscn")
```

## ColorRect Background

Full-screen background inside a CanvasLayer:

```
[node name="Background" type="ColorRect" parent="."]
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.15, 0.15, 0.2, 1)
```

Dark colors that work well:
- Space: `Color(0.15, 0.15, 0.2, 1)`
- Forest: `Color(0.1, 0.2, 0.1, 1)`
- Desert: `Color(0.3, 0.25, 0.15, 1)`

## Control Node Covering _draw()

**CRITICAL GOTCHA**: A Control node (ColorRect, Label, etc.) as child of Node2D renders ON TOP of the parent's `_draw()`, making drawn content invisible.

```gdscript
# BAD — ColorRect covers Node2D._draw()
# Node2D -> ColorRect

# GOOD — Use CanvasLayer for UI overlays
# Node2D -> CanvasLayer -> ColorRect

# GOOD — Draw backgrounds in _draw() directly
func _draw() -> void:
    draw_rect(Rect2(0, 0, 1024, 600), Color.BLACK)
```

## Common UI Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| No CanvasLayer | UI scrolls with camera | Wrap UI in CanvasLayer |
| Labels use `position` instead of `offset` | Anchor system breaks | Use `offset_left/top/right/bottom` |
| UI drawn before game | Z-order wrong | CanvasLayer renders on top by default |
| No theme override for color | White text on white bg | Add `theme_override_colors/font_color` |
| Control under Node2D covers _draw() | Drawn content invisible | Use CanvasLayer or draw in `_draw()` |
