---
name: event-bus
description: "Decoupled communication via global event bus. Triggers on: event bus, signal bus, global events, cross-system, decoupled."
---

# Event Bus / Signal Bus Pattern

Global event system for decoupled cross-system communication in Godot.

## Global Event Bus Autoload

```gdscript
# event_bus.gd — register as autoload in project.godot
extends Node

# Game Events
signal enemy_died(position: Vector2, points: int)
signal player_hit(damage: int)
signal player_died

# UI Events
signal score_changed(new_score: int)
signal health_changed(new_health: int)
signal game_paused(is_paused: bool)

# Level Events
signal level_completed(level_number: int)
signal checkpoint_reached(checkpoint_id: String)
```

## Emitting Events

```gdscript
# Any node can emit — no coupling needed
EventBus.enemy_died.emit(global_position, 100)
EventBus.score_changed.emit(new_score)
EventBus.player_hit.emit(damage)
```

## Listening to Events

```gdscript
func _ready() -> void:
    EventBus.enemy_died.connect(_on_enemy_died)
    EventBus.score_changed.connect(_on_score_changed)

func _on_enemy_died(position: Vector2, points: int) -> void:
    spawn_particles(position)
    add_score(points)

func _on_score_changed(new_score: int) -> void:
    score_label.text = "Score: %d" % new_score
```

## When to Use Events vs Direct Calls

| Use Events When | Use Direct Calls When |
|---|---|
| Sender doesn't know receivers | One clear owner |
| Multiple systems react | Single response expected |
| Loose coupling needed | Tight coupling is fine |
| Cross-scene communication | Same scene, same script |
| UI reacts to game state | Direct method is simpler |

## Typed Event Bus (Advanced)

For compile-time safety on event signatures:

```gdscript
# typed_events.gd
class_name TypedEvents

# Type-safe signal declarations
signal enemy_died(position: Vector2, points: int)
signal item_collected(item_type: String, quantity: int)

# Validation wrapper
static func emit_enemy_died(position: Vector2, points: int) -> void:
    EventBus.enemy_died.emit(position, points)
```

## Event Patterns

### Request-Response

```gdscript
# Request
signal damage_requested(amount: int, source: Node2D)

# Response
signal damage_applied(amount: int, target: Node2D)
```

### State Change Broadcast

```gdscript
signal game_state_changed(old_state: GameState, new_state: GameState)

func transition_game_state(new_state: GameState) -> void:
    var old = current_game_state
    current_game_state = new_state
    game_state_changed.emit(old, new_state)
```

### Buffered Events

For events that may fire before listeners connect:

```gdscript
var _buffered_events: Dictionary = {}

func emit_buffered(event_name: String, data: Variant) -> void:
    if _listeners.has(event_name):
        _listeners[event_name].emit(data)
    else:
        _buffered_events[event_name] = data

func listen_buffered(event_name: String, callback: Callable) -> void:
    if _buffered_events.has(event_name):
        callback.call(_buffered_events[event_name])
        _buffered_events.erase(event_name)
    listen(event_name, callback)
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Events for everything | Use direct calls for simple parent-child |
| Missing disconnect on queue_free | Use CONNECT_ONE_SHOT or disconnect |
| Circular event chains | Redesign to one-directional flow |
| God event bus (100+ signals) | Split into domain-specific buses |
