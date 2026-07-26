---
name: godot-signals
description: "Godot signal system: declaration, emission, connection, and event-driven patterns. Triggers on: signals, emit, connect, events, communication."
---

# Godot Signal System

Event-driven communication between nodes without tight coupling.

## Declaration

```gdscript
signal health_changed(new_health: int)
signal died
signal enemy_died(position: Vector2, points: int)
```

## Emission

```gdscript
health_changed.emit(health)
died.emit()
enemy_died.emit(global_position, 100)
```

## Connection

### In Code (_ready)

```gdscript
func _ready() -> void:
    health_changed.connect(_on_health_changed)
    died.connect(_on_died)
```

### After Instantiation

```gdscript
var enemy = enemy_scene.instantiate()
enemy.enemy_died.connect(_on_enemy_died)
add_child(enemy)
```

### Godot 4 Syntax (NOT Godot 3)

```gdscript
# GOOD — Godot 4
hit.connect(_on_hit)
signal_name.connect(method_name)

# BAD — Godot 3 (deprecated, fails silently)
connect('hit', self, '_on_hit')
```

## Signal Arguments

Signals can carry data. Declare with typed parameters:

```gdscript
# Declaration
signal health_changed(new_health: int)
signal item_collected(item_name: String, value: int)

# Emission with values
health_changed.emit(health)
item_collected.emit("coin", 10)

# Callback receives arguments
func _on_health_changed(new_health: int) -> void:
    health_label.text = "HP: %d" % new_health
```

## Event Bus Pattern

For cross-system communication (e.g., UI reacting to game events):

```gdscript
# event_bus.gd (autoload)
signal enemy_died(position: Vector2, points: int)
signal player_hit(damage: int)
signal coin_collected(value: int)
```

```gdscript
# Any node can emit
EventBus.enemy_died.emit(global_position, 100)

# Any node can listen
func _ready() -> void:
    EventBus.enemy_died.connect(_on_enemy_died)
```

## One-Shot Connections

Auto-disconnect after first emission:

```gdscript
signal timeout
timeout.connect(_on_timeout, CONNECT_ONE_SHOT)
```

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Connect in `_process()` | Duplicate callbacks every frame | Connect once in `_ready()` |
| Godot 3 connect syntax | Silent failure | Use `signal.connect(method)` |
| Missing `.emit()` | Signal never fires | Always call `signal_name.emit()` |
| Connecting freed node | Crash or error | Use `CONNECT_ONE_SHOT` or disconnect on exit |
| Passing wrong arg count | Runtime error | Match declaration signature exactly |
