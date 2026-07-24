---
title: "Add Enemy AI to Your Game"
type: guide
category: feature
difficulty: intermediate
estimated_time: "1-2 hours"
prerequisites: ["add-physics.md", "add-collisions.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Add Enemy AI to Your Game

How to implement enemy AI with state machines and behavior patterns.

## Overview

**What you'll learn:**
- State machine pattern
- Patrol behavior
- Chase behavior
- Attack behavior
- Navigation with NavigationAgent

---

## State Machine Pattern

### Create base state machine

```gdscript
# state_machine.gd
extends Node

@export var initial_state: Node

var current_state: State
var states: Dictionary = {}

func _ready() -> void:
    for child in get_children():
        if child is State:
            states[child.name.to_lower()] = child
            child.state_machine = self
            child.player = owner

    if initial_state:
        current_state = initial_state
        current_state.enter()

func _process(delta: float) -> void:
    if current_state:
        current_state.process(delta)

func _physics_process(delta: float) -> void:
    if current_state:
        current_state.physics_process(delta)

func transition_to(new_state_name: String) -> void:
    var new_state = states.get(new_state_name.to_lower())
    if new_state:
        current_state.exit()
        current_state = new_state
        current_state.enter()
```

### Create base state

```gdscript
# state.gd
class_name State
extends Node

var state_machine: Node
var player: CharacterBody2D

func enter() -> void:
    pass

func exit() -> void:
    pass

func process(delta: float) -> void:
    pass

func physics_process(delta: float) -> void:
    pass
```

---

## Patrol Behavior

```gdscript
# patrol_state.gd
extends State

@export var patrol_speed: float = 100.0
@export var patrol_wait_time: float = 2.0

var patrol_points: Array[Vector2]
var current_point_index: int = 0
var wait_timer: float = 0.0
var is_waiting: bool = false

func enter() -> void:
    # Get patrol points from PatrolPath node
    var path = player.get_node_or_null("PatrolPath")
    if path:
        for child in path.get_children():
            if child is Marker2D:
                patrol_points.append(child.global_position)

func physics_process(delta: float) -> void:
    if is_waiting:
        wait_timer -= delta
        if wait_timer <= 0:
            is_waiting = false
        return

    if patrol_points.is_empty():
        return

    var target = patrol_points[current_point_index]
    var direction = player.global_position.direction_to(target)

    player.velocity = direction * patrol_speed
    player.move_and_slide()

    if player.global_position.distance_to(target) < 10.0:
        current_point_index = (current_point_index + 1) % patrol_points.size()
        is_waiting = true
        wait_timer = patrol_wait_time
```

---

## Chase Behavior

```gdscript
# chase_state.gd
extends State

@export var chase_speed: float = 150.0
@export var detection_range: float = 200.0

@onready var navigation_agent: NavigationAgent2D

func _ready() -> void:
    await player.ready
    navigation_agent = player.get_node("NavigationAgent2D")

func enter() -> void:
    pass

func physics_process(delta: float) -> void:
    var player_ref = get_tree().get_first_node_in_group("player")
    if not player_ref:
        return

    var distance = player.global_position.distance_to(player_ref.global_position)

    if distance > detection_range:
        state_machine.transition_to("Patrol")
        return

    navigation_agent.target_position = player_ref.global_position

    if navigation_agent.is_navigation_finished():
        return

    var next_position = navigation_agent.get_next_path_position()
    var direction = player.global_position.direction_to(next_position)

    player.velocity = direction * chase_speed
    player.move_and_slide()
```

---

## Attack Behavior

```gdscript
# attack_state.gd
extends State

@export var attack_range: float = 32.0
@export var attack_damage: int = 10
@export var attack_cooldown: float = 1.0

var cooldown_timer: float = 0.0

func physics_process(delta: float) -> void:
    var player_ref = get_tree().get_first_node_in_group("player")
    if not player_ref:
        return

    var distance = player.global_position.distance_to(player_ref.global_position)

    if distance > attack_range:
        state_machine.transition_to("Chase")
        return

    cooldown_timer -= delta
    if cooldown_timer <= 0:
        attack(player_ref)
        cooldown_timer = attack_cooldown

func attack(target: Node2D) -> void:
    if target.has_method("take_damage"):
        target.take_damage(attack_damage)
    # Play attack animation
```

---

## Simple State Machine (No Nodes)

For simpler enemies, use a direct state machine:

```gdscript
extends CharacterBody2D

enum State { IDLE, PATROL, CHASE, ATTACK, HURT }

const PATROL_SPEED = 100.0
const CHASE_SPEED = 150.0
const DETECTION_RANGE = 200.0
const ATTACK_RANGE = 32.0

var state: State = State.IDLE
var health: int = 3
var target: Node2D

func _physics_process(delta: float) -> void:
    match state:
        State.IDLE:
            idle_state(delta)
        State.PATROL:
            patrol_state(delta)
        State.CHASE:
            chase_state(delta)
        State.ATTACK:
            attack_state(delta)
        State.HURT:
            hurt_state(delta)

    # Always apply gravity
    if not is_on_floor():
        velocity.y += ProjectSettings.get_setting("physics/2d/default_gravity") * delta

    move_and_slide()

func idle_state(_delta: float) -> void:
    velocity = Vector2.ZERO
    if target and global_position.distance_to(target.global_position) < DETECTION_RANGE:
        state = State.CHASE

func patrol_state(delta: float) -> void:
    # Patrol logic here
    pass

func chase_state(delta: float) -> void:
    if not target:
        state = State.IDLE
        return

    var direction = global_position.direction_to(target.global_position)
    velocity = direction * CHASE_SPEED

    if global_position.distance_to(target.global_position) < ATTACK_RANGE:
        state = State.ATTACK

func attack_state(_delta: float) -> void:
    if target and target.has_method("take_damage"):
        target.take_damage(10)
    state = State.CHASE

func hurt_state(_delta: float) -> void:
    # Flash, knockback, etc.
    state = State.CHASE
```

---

## Gotchas

1. **Await player.ready**: NavigationAgent needs the player to exist
2. **Use groups**: `get_tree().get_first_node_in_group("player")` is cleaner
3. **Distance checks**: Use squared distance for performance
4. **State transitions**: Always call `.exit()` on old state
5. **Debug visuals**: Draw detection ranges in `_draw()` for debugging

---

## Cross-References

- [Add Physics Guide](add-physics.md) — Physics bodies and forces
- [Add Collisions Guide](add-collisions.md) — Collision setup
- [Script Patterns](../patterns/scripts.md) — Common GDScript patterns
- [Build 2D Platformer](build-2d-platformer.md) — Complete game example
