---
title: "Build Main Menu"
type: guide
category: ui
difficulty: beginner
estimated_time: "30-60 minutes"
prerequisites: []
version: "4.7"
created: "2026-07-24"
status: active
---

# Build Main Menu

How to create a title screen with navigation in Godot 4.7.

## Overview

**What you'll build:**
- Title screen with logo
- Play, Settings, Quit buttons
- Scene transitions
- Basic menu navigation

---

## Main Menu Scene

### Create main_menu.gd

```gdscript
extends Control

@onready var play_button: Button = $VBoxContainer/PlayButton
@onready var settings_button: Button = $VBoxContainer/SettingsButton
@onready var quit_button: Button = $VBoxContainer/QuitButton

func _ready() -> void:
    play_button.pressed.connect(_on_play_pressed)
    settings_button.pressed.connect(_on_settings_pressed)
    quit_button.pressed.connect(_on_quit_pressed)
    play_button.grab_focus()

func _on_play_pressed() -> void:
    get_tree().change_scene_to_file("res://scenes/main.tscn")

func _on_settings_pressed() -> void:
    get_tree().change_scene_to_file("res://scenes/settings.tscn")

func _on_quit_pressed() -> void:
    get_tree().quit()
```

### Create main_menu.tscn

```
[gd_scene load_steps=2]

[ext_resource type="Script" path="res://scripts/main_menu.gd" id="1"]

[node name="MainMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.1, 0.1, 0.15, 1)

[node name="VBoxContainer" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -100.0
offset_top = -100.0
offset_right = 100.0
offset_bottom = 100.0
grow_horizontal = 2
grow_vertical = 2
theme_override_constants/separation = 20

[node name="TitleLabel" type="Label" parent="VBoxContainer"]
layout_mode = 2
text = "MY GAME"
horizontal_alignment = 1

[node name="PlayButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "Play"

[node name="SettingsButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "Settings"

[node name="QuitButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "Quit"
```

---

## Scene Transitions

### Create scene_transition.gd

```gdscript
extends CanvasLayer

@onready var color_rect: ColorRect = $ColorRect

func fade_to_scene(scene_path: String) -> void:
    var tween = create_tween()
    tween.tween_property(color_rect, "color:a", 1.0, 0.5)
    await tween.finished
    get_tree().change_scene_to_file(scene_path)
    tween = create_tween()
    tween.tween_property(color_rect, "color:a", 0.0, 0.5)
```

---

## Gotchas

1. **Grab focus**: Call `grab_focus()` on first button for keyboard navigation
2. **Scene tree**: Use `get_tree().change_scene_to_file()` for transitions
3. **Quit**: Always call `get_tree().quit()` for clean exit
4. **Autoload menus**: Consider making menu an autoload for persistence

---

## Cross-References

- [UI Patterns](../patterns/ui.md) — UI best practices
- [Build Settings](build-settings.md) — Settings menu
- [Build Transitions](build-transitions.md) — Transition effects
