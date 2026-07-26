---
name: state-machine
description: "State machine pattern for game flow and character behavior. Triggers on: state, state machine, FSM, transition, animation state, game flow."
---

# State Machine Pattern in Godot

Explicit states with transition rules for predictable game behavior.

## Enum-Based State Machine

```gdscript
extends CharacterBody2D

enum State { IDLE, RUNNING, JUMPING, FALLING, ATTACKING }
var current_state: State = State.IDLE

func _physics_process(delta: float) -> void:
    match current_state:
        State.IDLE: _idle_state(delta)
        State.RUNNING: _running_state(delta)
        State.JUMPING: _jumping_state(delta)
        State.FALLING: _falling_state(delta)
        State.ATTACKING: _attacking_state(delta)

func transition_to(new_state: State) -> void:
    if current_state == new_state:
        return
    _exit_state(current_state)
    current_state = new_state
    _enter_state(new_state)

func _exit_state(old_state: State) -> void:
    match old_state:
        State.ATTACKING: _end_attack()

func _enter_state(new_state: State) -> void:
    match new_state:
        State.ATTACKING: _begin_attack()

func _idle_state(_delta: float) -> void:
    if Input.is_action_pressed("move_right") or Input.is_action_pressed("move_left"):
        transition_to(State.RUNNING)
    if Input.is_action_just_pressed("jump"):
        transition_to(State.JUMPING)
```

## State Object Pattern (Scalable)

For complex games, use separate state scripts:

```gdscript
# state.gd — base class
class_name State
extends Node

var entity: CharacterBody2D

func enter() -> void:
    pass

func exit() -> void:
    pass

func update(delta: float) -> void:
    pass

func physics_update(delta: float) -> void:
    pass
```

```gdscript
# idle_state.gd
class_name IdleState
extends State

func enter() -> void:
    entity.velocity = Vector2.ZERO
    entity.sprite.play("idle")

func physics_update(delta: float) -> void:
    if Input.get_axis("move_left", "move_right") != 0:
        get_parent().transition_to("Running")
    elif Input.is_action_just_pressed("jump"):
        get_parent().transition_to("Jumping")
```

```gdscript
# state_machine.gd
extends Node

@export var initial_state: State
var current_state: State
var states: Dictionary = {}

func _ready() -> void:
    for child in get_children():
        if child is State:
            states[child.name.to_lower()] = child
            child.entity = get_parent()
    current_state = initial_state
    current_state.enter()

func _physics_process(delta: float) -> void:
    current_state.physics_update(delta)

func transition_to(state_name: String) -> void:
    current_state.exit()
    current_state = states[state_name]
    current_state.enter()
```

## Transition Rules

Define explicit guard conditions:

```gdscript
func can_jump() -> bool:
    return is_on_floor()

func can_attack() -> bool:
    return current_state != State.ATTACKING and attack_cooldown.is_stopped()
```

## Hierarchical State Machines

For nested states (e.g., grounded vs airborne):

```
MovementState
├── GroundedState
│   ├── IdleState
│   └── RunningState
└── AirborneState
    ├── JumpingState
    └── FallingState
```

## AnimationTree Integration

Use AnimationTree for visual state blending:

```gdscript
func _enter_state(new_state: State) -> void:
    match new_state:
        State.RUNNING:
            animation_tree["parameters/run/blend_position"] = velocity.x
            animation_state.travel("run")
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| State with nested ifs | Use match statement |
| Missing transition guards | Add condition checks before transitioning |
| State logic in _process | Keep logic in state methods |
| God state (handles everything) | Split into focused state objects |
