---
title: "Object Keep Format (OKF) Reference"
type: guide
version: "4.7"
created: "2026-07-26"
status: active
---

# Object Keep Format (OKF) Reference

Structured data format for game resources in Godot 4.x. OKF provides a
human-readable, versionable format for defining game objects.

## What is OKF?

OKF is a pattern for organizing game data as structured text files (`.tres`
or `.cfg`) that are:
- Human-readable in text editors
- Version-control friendly (mergeable)
- Editor-compatible (Godot Inspector editable)
- Type-safe (typed Resource classes)

## Core Principle

Separate DATA from BEHAVIOR:
- **Data** = Resource files (`.tres`, `.cfg`) define what an object IS
- **Behavior** = Scripts (`.gd`) define what an object DOES

## Pattern: Resource + .tres Data Files

```gdscript
# weapon_data.gd
class_name WeaponData extends Resource
@export var weapon_name: String = "Sword"
@export var damage: int = 10
@export var attack_speed: float = 1.0
@export var range: float = 32.0
@export var icon: Texture2D
```

```
# weapons/sword.tres
[gd_resource type="Resource" script_class="WeaponData" load_steps=2 format=3]
[ext_resource type="Script" path="res://scripts/weapon_data.gd" id="1"]
[resource]
script = ExtResource("1")
weapon_name = "Sword"
damage = 10
attack_speed = 1.2
range = 36.0
```

## Pattern: Data Tables

Organize related data in directories:

```
data/
├── weapons/
│   ├── sword.tres
│   ├── axe.tres
│   └── staff.tres
├── enemies/
│   ├── goblin.tres
│   ├── orc.tres
│   └── dragon.tres
└── items/
    ├── health_potion.tres
    └── mana_crystal.tres
```

## Pattern: Data Loading Service

```gdscript
# data_manager.gd (autoload)
extends Node

var _cache: Dictionary = {}

func load_weapon(weapon_id: String) -> WeaponData:
    var path = "res://data/weapons/%s.tres" % weapon_id
    if not _cache.has(path):
        _cache[path] = load(path)
    return _cache[path]

func load_all_weapons() -> Array[WeaponData]:
    var weapons: Array[WeaponData] = []
    var dir = DirAccess.open("res://data/weapons/")
    if dir:
        dir.list_dir_begin()
        var file = dir.get_next()
        while file != "":
            if file.ends_with(".tres"):
                weapons.append(load_weapon(file.get_basename()))
            file = dir.get_next()
    return weapons
```

## Pattern: Variant Inheritance

```gdscript
# base_item.gd
class_name BaseItem extends Resource
@export var item_name: String
@export var description: String
@export var icon: Texture2D
@export var stackable: bool = true

# weapon_item.gd
class_name WeaponItem extends BaseItem
@export var damage: int
@export var attack_speed: float

# armor_item.gd
class_name ArmorItem extends BaseItem
@export var defense: int
@export var slot: EquipmentSlot
```

## Pattern: Configuration Files

For game-wide settings:

```gdscript
# game_config.gd
class_name GameConfig extends Resource
@export var player_speed: float = 200.0
@export var gravity: float = 980.0
@export var max_enemies_per_wave: int = 20
@export var difficulty_curve: Curve
```

## Benefits

- **Designer-friendly**: Edit .tres files without touching code
- **Git-friendly**: Text-based, mergeable diffs
- **Type-safe**: class_name gives compile-time checks
- **Cacheable**: Godot caches loaded Resources automatically
- **Reusable**: Same data file can be used by multiple scenes

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hardcoding data in scripts | Move to .tres Resource files |
| Loading without cache | Use preload or cache dictionary |
| Mutating shared resources | Duplicate before modifying |
| Missing class_name | Add for type safety |
