---
name: godot-scene-tree
description: "Godot node hierarchy design, composition patterns, and scene tree architecture. Triggers on: scene tree, node hierarchy, composition, node types, scene design."
---

# Godot Scene Tree Architecture

How to design node hierarchies and compose scenes.

## Node Type Selection

| Type | Use Case | Movement | Physics |
|------|----------|----------|---------|
| `Node2D` / `Node3D` | Generic container with transform | Manual | None |
| `CharacterBody2D/3D` | Player, enemies, NPCs | `move_and_slide()` | Full collision response |
| `StaticBody2D/3D` | Walls, floors, obstacles | None | Blocks other bodies |
| `RigidBody2D/3D` | Physics objects, projectiles | Engine-driven | Full physics simulation |
| `Area2D/3D` | Triggers, collectibles | Manual or none | Overlap detection only |
| `Control` | UI elements | N/A | N/A |
| `CanvasLayer` | HUD/overlay | N/A | N/A |

## Composition Rules

### One Task Per Node

Don't cram rendering, physics, and UI into one node. Split responsibilities:

```
CharacterBody2D (movement + collision)
├── Sprite2D (visual only)
├── CollisionShape2D (physics shape only)
├── AnimationPlayer (animation only)
└── Camera2D (follow camera only)
```

### Visual + Collision Pairs

Every physics body needs a CollisionShape child. No exceptions.

```
# BAD — no collision
CharacterBody2D
└── Sprite2D

# GOOD — collision paired with visual
CharacterBody2D
├── Sprite2D
└── CollisionShape2D
```

### Unique Names for Script Access

Use `unique_name_in_owner = true` for nodes accessed by `%NodeName`:

```
# In .tscn:
[node name="ScoreLabel" type="Label" parent="." unique_name_in_owner=true]

# In script:
@onready var score_label: Label = %ScoreLabel
```

## Common Scene Patterns

### Character

```
CharacterBody2D
├── Sprite2D / Polygon2D
├── CollisionShape2D
├── AnimationPlayer
└── Camera2D (optional)
```

### Enemy

```
CharacterBody2D
├── Sprite2D
├── CollisionShape2D
├── Area2D (hitbox)
│   └── CollisionShape2D
└── AnimationPlayer
```

### Collectible

```
Area2D
├── Sprite2D
└── CollisionShape2D
```

### Wall

```
StaticBody2D
└── CollisionShape2D
```

### HUD

```
CanvasLayer
├── MarginContainer
│   ├── ScoreLabel
│   └── HealthLabel
└── PauseMenu (Control, hidden)
```

### Level

```
Node2D
├── TileMapLayer
├── Player (instance)
├── Enemies (node container)
│   └── [instanced enemy scenes]
└── Collectibles (node container)
```

## Anti-Patterns

- Mixing 2D and 3D nodes in the same branch
- Putting CollisionShape under plain Node2D (needs physics body parent)
- Nesting scenes too deeply (keep under 4 levels)
- Using absolute paths (`/root/Main/Player`) instead of relative or group-based
