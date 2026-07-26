---
name: ecs-pattern
description: "Entity-Component-System pattern in Godot. Triggers on: ECS, entity, component, system, composition, data-driven."
---

# Entity-Component-System (ECS) in Godot

Data-oriented architecture for flexible game object composition.

## Core Concepts

### Entities
Nodes that represent game objects. Each entity has a unique ID (instance_id or custom).

```gdscript
# entity.gd — base entity node
extends Node2D
class_name Entity

var entity_id: int

func _ready() -> void:
    entity_id = get_instance_id()
```

### Components
Data containers attached as child nodes. No logic — just state.

```gdscript
# health_component.gd
extends Node
class_name HealthComponent

signal health_changed(new_health: int)
signal died

@export var max_health: int = 100
var health: int

func take_damage(amount: int) -> void:
    health = clamp(health - amount, 0, max_health)
    health_changed.emit(health)
    if health <= 0:
        died.emit()
```

### Systems
Nodes that process entities by component type. All logic lives here.

```gdscript
# movement_system.gd
extends Node

func _physics_process(delta: float) -> void:
    for entity in get_tree().get_nodes_in_group("movable"):
        var movement: MovementComponent = entity.get_node_or_null("MovementComponent")
        var health: HealthComponent = entity.get_node_or_null("HealthComponent")
        if movement and health and health.health > 0:
            entity.position += movement.velocity * delta
```

## Godot-Specific ECS Patterns

### Scene Tree as Entity Registry
Use groups to tag entities for system processing:

```gdscript
# On entity creation
add_to_group("enemies")
add_to_group("damageable")

# System queries
var enemies = get_tree().get_nodes_in_group("enemies")
```

### Component as Child Node
Attach components as children — Godot's tree structure IS the entity:

```
Enemy (Entity)
├── Sprite2D (visual)
├── CollisionShape2D (physics)
├── HealthComponent (data)
├── MovementComponent (data)
└── AIComponent (data)
```

### Resource as Component
For pure data without scene tree overhead:

```gdscript
# enemy_stats.gd
class_name EnemyStats extends Resource
@export var max_health: int = 50
@export var speed: float = 150.0
@export var damage: int = 10
```

## When to Use ECS vs Traditional

| Use ECS When | Use Traditional When |
|---|---|
| Many entity variations | Few entity types |
| Behaviors need mixing | Behaviors are fixed |
| Runtime composition needed | Compile-time is fine |
| Data-driven design preferred | Simple hierarchy works |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Components with logic | Move logic to Systems |
| Systems with state | State belongs in Components |
| God object entity | Split into focused components |
| Hardcoded component lookups | Use groups for system queries |
