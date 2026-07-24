# Physics & Collision

Godot collision system basics: layers, masks, body types, and common patterns.

## Collision Layers vs Masks

Layers define **where** a node exists. Masks define **what** a node collides with.

| Property | Purpose | Example |
|----------|---------|---------|
| `collision_layer` | "I am on these layers" | Player = layer 1 |
| `collision_mask` | "I collide with these layers" | Player mask = layers 2,3 (enemies + walls) |

Both are **bitmasks** — values are powers of 2:

| Layer | Bitmask Value |
|-------|--------------|
| Layer 1 | `1` |
| Layer 2 | `2` |
| Layer 3 | `4` |
| Layer 4 | `8` |
| Layers 1+2 | `3` (1 + 2) |
| Layers 1+2+3 | `7` (1 + 2 + 4) |

```gdscript
# Player: on layer 1, collides with enemies (2) and walls (3)
collision_layer = 1
collision_mask = 6  # 2 + 4 = layers 2 and 3

# Enemy: on layer 2, collides with player (1) and walls (3)
collision_layer = 2
collision_mask = 5  # 1 + 4 = layers 1 and 3

# Wall: on layer 3, collides with nothing (static)
collision_layer = 4
collision_mask = 0
```

---

## Body Types

| Type | Use Case | Movement | Physics |
|------|----------|----------|---------|
| `CharacterBody2D` | Player, enemies, NPCs | Manual via `move_and_slide()` | Full collision response |
| `Area2D` | Collectibles, triggers, hitboxes | Manual or none | Overlap detection only |
| `StaticBody2D` | Walls, floors, obstacles | None | Blocks other bodies |
| `RigidBody2D` | Physics objects, projectiles | Engine-driven | Full physics simulation |

### When to Use What

- **Need to move and collide?** → `CharacterBody2D`
- **Need to detect overlap without blocking?** → `Area2D`
- **Need to block movement but never move?** → `StaticBody2D`
- **Need realistic physics (bounce, gravity, forces)?** → `RigidBody2D`

---

## Area2D Signals

```gdscript
extends Area2D

func _ready() -> void:
    body_entered.connect(_on_body_entered)
    body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node2D) -> void:
    if body is CharacterBody2D:
        print(body.name + " entered area")

func _on_body_exited(body: Node2D) -> void:
    print(body.name + " left area")
```

---

## Common Collision Patterns

### Player vs Enemy

```
Player (CharacterBody2D)
├── layer: 1 (player)
├── mask: 6 (enemies=2 + walls=4)

Enemy (CharacterBody2D)
├── layer: 2 (enemy)
├── mask: 5 (player=1 + walls=4)

Wall (StaticBody2D)
├── layer: 4 (wall)
├── mask: 0 (nothing — walls don't seek collisions)
```

### Collectible (overlap, no block)

```
Coin (Area2D)
├── layer: 0 (invisible to physics)
├── mask: 1 (detects player only)
```

### One-way platform

```
Platform (StaticBody2D)
├── collision_mask = 1  # only player
├── collision_layer = 4
└── one_way_collision = true  # can jump through from below
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Using `1, 2, 3` as layer values | Only layer 1 works | Use bitmasks: `1`, `2`, `4`, `8` |
| Enemy mask includes enemy layer | Enemies collide with each other | Remove own layer from mask |
| Area2D with collision_layer set | Area blocks movement | Set `collision_layer = 0` for detection-only |
| Missing CollisionShape2D | No collision at all | Add CollisionShape2D with a shape resource |
| Wrong body type for use case | Physics bugs | See "When to Use What" table above |
