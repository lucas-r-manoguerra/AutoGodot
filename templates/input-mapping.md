# Input Mapping

How to configure and use Input Actions in Godot 4.7.

## Setting Up Input Actions

Define actions in `project.godot` under `[input]`:

```ini
[input]

move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":97,"location":0,"echo":false,"script":null)
]
}
move_right={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":68,"key_label":0,"unicode":100,"location":0,"echo":false,"script":null)
]
}
```

### Simpler Approach (in code)

Register input actions programmatically in `_ready()`:

```gdscript
func _ready() -> void:
    # Only add if not already defined
    if not InputMap.has_action("move_left"):
        InputMap.add_action("move_left")
        var ev = InputEventKey.new()
        ev.physical_keycode = KEY_A
        InputMap.action_add_event("move_left", ev)
```

---

## Common Action Names

Use consistent naming across your project:

| Action | Keys | Purpose |
|--------|------|---------|
| `move_left` | A, Left | Move left |
| `move_right` | D, Right | Move right |
| `move_up` | W, Up | Move up |
| `move_down` | S, Down | Move down |
| `jump` | Space, W | Jump |
| `attack` | J, Enter | Attack |
| `interact` | E | Interact with objects |
| `pause` | Escape | Pause game |

---

## Reading Input

### Movement (Vector)

```gdscript
# Best for 4-directional movement
var direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
velocity = direction * speed
move_and_slide()
```

### Movement (Axis)

```gdscript
# Best for horizontal-only (platformers)
var horizontal = Input.get_axis("move_left", "move_right")
velocity.x = horizontal * speed
```

### Button Press (Single Frame)

```gdscript
# Fires once per press, not every frame
if Input.is_action_just_pressed("jump") and is_on_floor():
    velocity.y = JUMP_VELOCITY

# Also available:
if Input.is_action_just_released("jump"):
    pass  # button released this frame
```

### Button Held

```gdscript
# Fires every frame while held
if Input.is_action_pressed("attack"):
    shoot()
```

---

## Multiple Keys Per Action

Each action can have multiple key bindings:

```
move_left:
  - A (physical_keycode: 65)
  - Left Arrow (physical_keycode: 4194319)
```

Both keys trigger the same action. Godot handles this automatically.

---

## Gamepad Support

Add gamepad events to actions:

```gdscript
# Add joystick left to move_left action
var joy_ev = InputEventJoystickMotion.new()
joy_ev.axis = JOY_AXIS_LEFT_X
joy_ev.axis_value = -1.0
InputMap.action_add_event("move_left", joy_ev)
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Typo in action name | Input silently ignored | Double-check spelling matches `project.godot` |
| Using `is_action_pressed` for jump | Character jumps multiple times | Use `is_action_just_pressed` for single-press actions |
| Checking raw key codes | Breaks on different keyboards | Use InputMap actions, not `KEY_A` directly |
| Missing action in project.godot | "Unknown action" warning | Define all actions before using them |
| Using `_process` for physics input | Inconsistent behavior | Read input in `_physics_process` for movement |
