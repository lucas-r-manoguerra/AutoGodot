---
type: Checklist
title: Project Structure
description: Recommended folder layout, naming conventions, scaling strategies, and anti-patterns for Godot projects
tags:
  - checklist
  - project-structure
  - folder-layout
  - naming
  - scaling
  - autoload
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-24T15:00:00Z"
---

# Project Structure

Organize your Godot project for long-term scalability. A clean folder structure prevents chaos when the project grows.

## Recommended Folder Layout

```
project/
├── project.godot
├── scenes/
│   ├── main.tscn
│   ├── player.tscn
│   └── enemies/
│       ├── enemy_basic.tscn
│       └── enemy_boss.tscn
├── scripts/
│   ├── player.gd
│   └── enemies/
│       ├── enemy_basic.gd
│       └── enemy_boss.gd
├── assets/
│   ├── sprites/
│   ├── audio/
│   │   ├── music/
│   │   └── sfx/
│   ├── fonts/
│   └── themes/
│       └── default_theme.tres
├── data/
│   └── levels/
│       ├── level_01.tscn
│       └── level_02.tscn
└── autoloads/
    ├── game_manager.gd
    └── audio_manager.gd
```

---

## File Naming Conventions

- **snake_case** for all files and folders: `enemy_basic.gd`, not `EnemyBasic.gd`
- **Scene-script pairing**: `player.tscn` ↔ `player.gd` — same name, different extension
- **Prefix with type** when clarity helps: `ui_hud.tscn`, `sfx_explosion.wav`
- **No spaces**, no special characters, no uppercase in file names

---

## Scene Organization

### One Scene Per File

Each `.tscn` file should represent one logical entity or screen. Don't put the player AND the enemy AND the UI in one scene.

### Nested Scene Composition

Instance scenes inside other scenes using `PackedScene`:

```
main.tscn
├── Background (ColorRect)
├── Player (instance of player.tscn)
├── Enemies (Node2D container)
│   └── Enemy (instance of enemy.tscn)
└── HUD (instance of game_ui.tscn)
```

Load dynamically with:
```gdscript
var enemy_scene = preload("res://scenes/enemies/enemy_basic.tscn")
var enemy = enemy_scene.instantiate()
add_child(enemy)
```

---

## Resource Organization

### Sprites
Keep in `assets/sprites/`. Use sprite sheets (atlas textures) when possible — fewer files, better batching.

### Audio
Split into `assets/audio/music/` and `assets/audio/sfx/`. Name with prefix: `sfx_explosion.wav`, `music_level01.ogg`.

### Themes
Shared UI themes go in `assets/themes/`. Create a `default_theme.tres` and apply it to your root CanvasLayer.

---

## Autoloads (Singletons)

Use autoload for systems that must exist globally:

```gdscript
# autoloads/game_manager.gd
extends Node

signal score_changed(new_score: int)
signal health_changed(new_health: int)
signal game_over

var score: int = 0
var health: int = 100

func add_score(points: int) -> void:
    score += points
    score_changed.emit(score)

func take_damage(amount: int) -> void:
    health = maxi(0, health - amount)
    health_changed.emit(health)
    if health <= 0:
        game_over.emit()
```

Register in `project.godot`:
```ini
[autoload]
GameManager="*res://autoloads/game_manager.gd"
```

Access from anywhere: `GameManager.take_damage(10)`

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Everything in root folder | Can't find anything | Organized subfolders |
| 500+ line scripts | Unmaintainable | Split into components |
| Inline resources in .tscn | Scene files bloat to 1000+ lines | External `.tres` resource files |
| No naming convention | Team confusion | Enforce snake_case |
| Monolithic scenes | Hard to reuse parts | Nested scene composition |
| Copy-pasting scenes | Divergent variants | Scene inheritance or composition |
| Hardcoding paths | Breaks when reorganizing | Use `preload()` with relative paths |

---

## Scaling Strategies

1. **Autoload for singletons**: GameManager, AudioManager, SceneManager — global systems that never get freed
2. **Scene composition**: Build complex entities from smaller reusable scenes (player = body + weapon + health component)
3. **Dynamic level loading**: Load levels as scenes, not hardcoded in main
4. **Resource-based data**: Store enemy stats, item definitions in `.tres` files, not hardcoded in scripts
5. **Signal-driven communication**: Components talk via signals, not direct node references

---

## Related

- [scene/structures.md](../scene/structures.md) - .tscn file anatomy and ext_resource patterns
- [reference/node-paths.md](../reference/node-paths.md) - Node referencing with $ and get_node()
