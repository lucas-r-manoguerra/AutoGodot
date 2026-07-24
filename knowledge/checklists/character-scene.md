---
type: Checklist
title: Character Scene Checklist
description: Mandatory nodes every character scene must have - visual, collision, and script
tags:
  - checklist
  - character
  - character-body
  - area2d
  - static-body
  - collision
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-24T15:00:00Z"
---

# Character Scene Checklist

Every character scene **must** have a visual node and a collision node. Without visual = invisible. Without collision = no physics interactions.

## The Golden Rule

```
Root Node (CharacterBody2D/Area2D/StaticBody2D)
├── Visual Node (Polygon2D or Sprite2D)
├── Collision Shape (CollisionShape2D with shape resource)
└── Script (attached to root, extends root type)
```

**Never ship a character scene without all three children.**

---

## CharacterBody2D

Use for: player, enemies, NPCs — anything that moves and collides.

- [ ] Root: `CharacterBody2D`
- [ ] Visual: `Polygon2D` (colored shape) or `Sprite2D` (texture)
- [ ] Collision: `CollisionShape2D` with `RectangleShape2D` or `CircleShape2D`
- [ ] Script: Extends `CharacterBody2D`, uses `move_and_slide()`

```gdscript
# player.gd — minimal CharacterBody2D
extends CharacterBody2D

const SPEED = 200.0

func _physics_process(delta: float) -> void:
    var direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
    self.velocity = direction * SPEED
    move_and_slide()
```

---

## Area2D

Use for: collectibles, triggers, hitboxes, projectiles.

- [ ] Root: `Area2D`
- [ ] Visual: `Polygon2D` or `Sprite2D`
- [ ] Collision: `CollisionShape2D` with shape
- [ ] Script: Extends `Area2D`, connects `body_entered` or `area_entered`

```gdscript
# coin.gd — minimal Area2D
extends Area2D

func _ready() -> void:
    body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node2D) -> void:
    if body.has_method("collect"):
        body.collect()
    queue_free()
```

---

## StaticBody2D

Use for: walls, floors, platforms, obstacles.

- [ ] Root: `StaticBody2D`
- [ ] Visual: `Polygon2D` or `Sprite2D`
- [ ] Collision: `CollisionShape2D` with shape

No script usually needed — static bodies just block movement.

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| No Polygon2D/Sprite2D | Grey or invisible character | Add visual child node |
| No CollisionShape2D | Character passes through everything | Add CollisionShape2D with shape |
| CollisionShape2D without shape | Editor warning, no collision | Assign RectangleShape2D or CircleShape2D |
| Script on child node | Signals fire on wrong node | Move script to root CharacterBody2D |
| Using `_process` for movement | Inconsistent physics | Use `_physics_process` |
| Passing velocity to `move_and_slide(velocity)` | Godot 3.x error | Use `self.velocity = val` then `move_and_slide()` |

---

## Related

- [patterns/scripts.md](../patterns/scripts.md) - GDScript movement and health patterns
- [scene/structures.md](../scene/structures.md) - Complete .tscn character scene example
- [reference/physics-collision.md](../reference/physics-collision.md) - Collision layers, masks, and body types
