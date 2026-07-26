---
name: godot-physics
description: "Godot physics bodies, collision layers, masks, Area2D patterns. Triggers on: physics, collision, layers, masks, CharacterBody, Area2D, StaticBody, RigidBody."
---

# Godot Physics & Collision

Collision layers, masks, body types, and common patterns.

## Collision Layers vs Masks

Layers define **where** a node exists. Masks define **what** it collides with.

| Property | Purpose | Example |
|----------|---------|---------|
| `collision_layer` | "I am on these layers" | Player = layer 1 |
| `collision_mask` | "I collide with these layers" | Player mask = layers 2,3 |

Both are bitmasks (powers of 2):

| Layer | Bitmask | Combined |
|-------|---------|----------|
| 1 | `1` | — |
| 2 | `2` | — |
| 3 | `4` | — |
| 1+2 | — | `3` |
| 1+2+3 | — | `7` |

```gdscript
# Player: on layer 1, collides with enemies (2) and walls (3)
collision_layer = 1
collision_mask = 6  # 2 + 4

# Enemy: on layer 2, collides with player (1) and walls (3)
collision_layer = 2
collision_mask = 5  # 1 + 4

# Wall: on layer 3, collides with nothing (static)
collision_layer = 4
collision_mask = 0
```

## Body Types Decision

- **Need to move and collide?** → `CharacterBody2D`
- **Need to detect overlap without blocking?** → `Area2D`
- **Need to block movement but never move?** → `StaticBody2D`
- **Need realistic physics (bounce, gravity)?** → `RigidBody2D`

## Area2D Signals

```gdscript
extends Area2D

func _ready() -> void:
    body_entered.connect(_on_body_entered)
    body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node2D) -> void:
    if body is CharacterBody2D:
        print(body.name + " entered area")
```

## Common Patterns

### Collectible (overlap, no block)

```
Coin (Area2D)
├── layer: 0 (invisible to physics)
├── mask: 1 (detects player only)
├── Sprite2D
└── CollisionShape2D
```

### One-Way Platform

```
Platform (StaticBody2D)
├── collision_mask = 1
├── collision_layer = 4
└── one_way_collision = true
```

### Hitbox / Hurtbox

```
Player (CharacterBody2D)
├── layer: 1
├── mask: 6
├── Hitbox (Area2D)
│   ├── layer: 0
│   └── mask: 2 (detects enemies)
└── Hurtbox (Area2D)
    ├── layer: 2
    └── mask: 0
```

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Using `1, 2, 3` as layer values | Only layer 1 works | Use bitmasks: `1`, `2`, `4`, `8` |
| Enemy mask includes enemy layer | Enemies collide with each other | Remove own layer from mask |
| Area2D with collision_layer set | Area blocks movement | Set `collision_layer = 0` for detection-only |
| Missing CollisionShape2D | No collision at all | Add CollisionShape2D with a shape |
| Wrong body type | Physics bugs | See "Body Types Decision" above |
