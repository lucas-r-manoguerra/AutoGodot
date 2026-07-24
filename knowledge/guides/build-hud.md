---
title: "Build HUD"
type: guide
category: ui
difficulty: beginner
estimated_time: "30-60 minutes"
prerequisites: ["build-main-menu.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Build HUD

How to create an in-game heads-up display.

## Overview

**What you'll build:**
- Health bar with smooth animation
- Score display
- Mini-map placeholder
- Pause menu integration

---

## Health Bar

### Create health_bar.gd

```gdscript
extends ProgressBar

@onready var fill: ColorRect = $Fill
@onready var damage_fill: ColorRect = $DamageFill

var current_health: float = 100.0
var max_health: float = 100.0
var damage_timer: float = 0.0

func _process(delta: float) -> void:
    # Smooth damage trail
    if damage_fill.value > value:
        damage_timer += delta * 2.0
        damage_fill.value = lerp(damage_fill.value, value, damage_timer)

func set_health(new_health: float) -> void:
    current_health = clampf(new_health, 0.0, max_health)
    var target_value = (current_health / max_health) * 100.0
    var tween = create_tween()
    tween.tween_property(self, "value", target_value, 0.3)
    damage_timer = 0.0
```

### Create health_bar.tscn

```
[gd_scene load_steps=2]

[ext_resource type="Script" path="res://scripts/health_bar.gd" id="1"]

[node name="HealthBar" type="ProgressBar"]
custom_minimum_size = Vector2(200, 20)
max_value = 100.0
value = 100.0
show_percentage = false
script = ExtResource("1")

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.2, 0.2, 0.2, 1)

[node name="Fill" type="ProgressBar" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
max_value = 100.0
value = 100.0
tint_progress = Color(0.1, 0.8, 0.1, 1)
show_percentage = false

[node name="DamageFill" type="ProgressBar" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
max_value = 100.0
value = 100.0
tint_progress = Color(0.8, 0.1, 0.1, 0.6)
show_percentage = false
```

---

## Score Display

### Create score_display.gd

```gdscript
extends Label

var score: int = 0
var tween: Tween

func add_score(amount: int) -> void:
    score += amount
    _animate_score()

func _animate_score() -> void:
    if tween:
        tween.kill()
    tween = create_tween()
    tween.tween_property(self, "scale", Vector2(1.2, 1.2), 0.1)
    tween.tween_property(self, "scale", Vector2(1.0, 1.0), 0.1)
    text = "Score: %d" % score
```

---

## Pause Menu

### Create pause_menu.gd

```gdscript
extends CanvasLayer

@onready var panel: PanelContainer = $Panel

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    hide()

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_pressed("ui_cancel"):
        toggle_pause()

func toggle_pause() -> void:
    get_tree().paused = not get_tree().paused
    visible = get_tree().paused

func _on_resume_pressed() -> void:
    toggle_pause()

func _on_quit_pressed() -> void:
    get_tree().paused = false
    get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
```

---

## Gotchas

1. **CanvasLayer**: Use for UI to render above game
2. **process_mode**: Set to ALWAYS for pause menus
3. **Anchors**: Use anchors for responsive layout
4. **Z-index**: UI elements should have high z_index
5. **Input**: Block game input when UI is open

---

## Cross-References

- [UI Patterns](../patterns/ui.md) — UI best practices
- [Build Main Menu](build-main-menu.md) — Menu navigation
- [Optimize 2D](optimize-2d.md) — Performance tips
