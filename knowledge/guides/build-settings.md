---
title: "Build Settings Menu"
type: guide
category: ui
difficulty: beginner
estimated_time: "30-60 minutes"
prerequisites: ["build-main-menu.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Build Settings Menu

How to create a settings menu with audio/video controls.

## Overview

**What you'll build:**
- Audio volume sliders (Master, Music, SFX)
- Resolution and fullscreen options
- Settings persistence with ConfigFile

---

## Settings Data

### Create settings_manager.gd (Autoload)

```gdscript
extends Node

const SETTINGS_PATH = "user://settings.cfg"

var settings := {
    "master_volume": 1.0,
    "music_volume": 0.8,
    "sfx_volume": 1.0,
    "fullscreen": false,
    "resolution": Vector2i(1920, 1080)
}

func _ready() -> void:
    load_settings()
    apply_settings()

func save_settings() -> void:
    var config = ConfigFile.new()
    for key in settings:
        config.set_value("audio", key, settings[key])
    config.save(SETTINGS_PATH)

func load_settings() -> void:
    var config = ConfigFile.new()
    if config.load(SETTINGS_PATH) == OK:
        for key in settings:
            if config.has_section_key("audio", key):
                settings[key] = config.get_value("audio", key)

func apply_settings() -> void:
    AudioServer.set_bus_volume_db(0, linear_to_db(settings.master_volume))
    AudioServer.set_bus_volume_db(1, linear_to_db(settings.music_volume))
    AudioServer.set_bus_volume_db(2, linear_to_db(settings.sfx_volume))

    if settings.fullscreen:
        DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
    else:
        DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
        DisplayServer.window_set_size(settings.resolution)
```

---

## Settings UI

### Create settings_menu.gd

```gdscript
extends Control

@onready var master_slider: HSlider = $VBoxContainer/Master/MasterSlider
@onready var music_slider: HSlider = $VBoxContainer/Music/MusicSlider
@onready var sfx_slider: HSlider = $VBoxContainer/SFX/SFXSlider
@onready var fullscreen_check: CheckButton = $VBoxContainer/Fullscreen/FullscreenCheck
@onready var back_button: Button = $VBoxContainer/BackButton

var settings_manager: Node

func _ready() -> void:
    settings_manager = get_node("/root/SettingsManager")
    _load_ui_from_settings()
    back_button.pressed.connect(_on_back_pressed)
    master_slider.value_changed.connect(func(v): settings_manager.settings.master_volume = v)
    music_slider.value_changed.connect(func(v): settings_manager.settings.music_volume = v)
    sfx_slider.value_changed.connect(func(v): settings_manager.settings.sfx_volume = v)
    fullscreen_check.toggled.connect(func(v): settings_manager.settings.fullscreen = v)

func _load_ui_from_settings() -> void:
    master_slider.value = settings_manager.settings.master_volume
    music_slider.value = settings_manager.settings.music_volume
    sfx_slider.value = settings_manager.settings.sfx_volume
    fullscreen_check.button_pressed = settings_manager.settings.fullscreen

func _on_back_pressed() -> void:
    settings_manager.apply_settings()
    settings_manager.save_settings()
    get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
```

---

## Gotchas

1. **Decibels**: Godot uses dB for volume — convert with `linear_to_db()`
2. **Autoload**: SettingsManager should be an autoload singleton
3. **Persistence**: Save to `user://` for write access
4. **Reset**: Add a reset-to-defaults button

---

## Cross-References

- [Build Main Menu](build-main-menu.md) — Menu navigation
- [Audio Patterns](../patterns/audio.md) — Audio bus setup
