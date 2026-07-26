---
name: resource-pattern
description: "Data-driven design with Godot Resources. Triggers on: resource, .tres, data-driven, @export Resource, game data, configuration."
---

# Resource-Based Data Design

Data-driven approach using Godot's Resource system for game data.

## Custom Resource Classes

```gdscript
# enemy_data.gd
class_name EnemyData extends Resource

@export var enemy_name: String = "Goblin"
@export var max_health: int = 50
@export var speed: float = 150.0
@export var damage: int = 10
@export var attack_range: float = 32.0
@export var sprite_frame: Texture2D
@export var death_effect: PackedScene
```

## Using Resources in Scripts

```gdscript
extends CharacterBody2D

@export var data: EnemyData

@onready var sprite: Sprite2D = $Sprite2D

func _ready() -> void:
    if data:
        sprite.texture = data.sprite_frame
```

## .tres Files for Game Data

Create variations in the editor or as text:

```
[gd_resource type="Resource" script_class="EnemyData" load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemy_data.gd" id="1"]

[resource]
script = ExtResource("1")
enemy_name = "Orc Warrior"
max_health = 150
speed = 120.0
damage = 25
```

## Resource Inheritance for Variants

```gdscript
# base_enemy.gd
class_name BaseEnemyData extends Resource
@export var max_health: int = 50
@export var speed: float = 150.0

# flying_enemy.gd
class_name FlyingEnemyData extends BaseEnemyData
@export var flight_height: float = 200.0
@export var hover_speed: float = 50.0
```

## Loading and Caching

```gdscript
# Preload at compile time (fast, cached)
const ENEMY_DATA = preload("res://data/enemies/goblin.tres")

# Load at runtime (flexible, slower)
var data = load("res://data/enemies/%s.tres" % enemy_type)

# Cache frequently used resources
var _cache: Dictionary = {}

func get_data(key: String) -> Resource:
    if not _cache.has(key):
        _cache[key] = load("res://data/%s.tres" % key)
    return _cache[key]
```

## Resource Arrays

For collections of game data:

```gdscript
# wave_data.gd
class_name WaveData extends Resource
@export var wave_number: int
@export var enemies: Array[EnemyData] = []
@export var spawn_delay: float = 2.0
@export var bonus_points: int = 50
```

```gdscript
# level_data.gd
class_name LevelData extends Resource
@export var level_name: String
@export var waves: Array[WaveData] = []
@export var time_limit: float = 120.0
@export var music: AudioStream
```

## Data-Driven Design Patterns

### Configuration Objects

```gdscript
class_name GameConfig extends Resource
@export var player_speed: float = 200.0
@export var gravity: float = 980.0
@export var max_jumps: int = 2
@export var difficulty_scale: float = 1.0
```

### Loot Tables

```gdscript
class_name LootEntry extends Resource
@export var item_name: String
@export var drop_chance: float = 0.5
@export var min_quantity: int = 1
@export var max_quantity: int = 1

class_name LootTable extends Resource
@export var entries: Array[LootEntry] = []

func roll() -> LootEntry:
    for entry in entries:
        if randf() <= entry.drop_chance:
            return entry
    return null
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Load() every frame | Preload or cache resources |
| Resource without class_name | Add class_name for type safety |
| Mutating shared resources | Duplicate before modifying: `res.duplicate()` |
| Missing @export on Resource fields | Add @export for editor visibility |
