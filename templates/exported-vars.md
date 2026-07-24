# Exported Variables

How to expose variables to the Inspector with `@export` and `@onready`.

## @export

Makes a variable editable in the Godot Inspector. The engine handles serialization.

```gdscript
extends CharacterBody2D

@export var speed: float = 200.0
@export var health: int = 100
@export var jump_force: float = -400.0
@export var coin_scene: PackedScene
```

Set values in the Inspector panel — no need to hardcode in scripts.

---

## @export with Type Hints

Different types show different Inspector widgets:

| Type | Inspector Widget | Example |
|------|-----------------|---------|
| `int` | Number field | `@export var health: int = 100` |
| `float` | Number field | `@export var speed: float = 200.0` |
| `String` | Text field | `@export var name: String = "Player"` |
| `bool` | Checkbox | `@export var invincible: bool = false` |
| `Color` | Color picker | `@export var trail_color: Color = Color.WHITE` |
| `Vector2` | X/Y fields | `@export var spawn_offset: Vector2 = Vector2.ZERO` |
| `PackedScene` | Scene picker | `@export var bullet_scene: PackedScene` |
| `Texture2D` | Texture picker | `@export var icon: Texture2D` |

---

## @export with Range

Limit numeric values with `@export_range`:

```gdscript
@export_range(0, 100) var health: int = 100
@export_range(0.0, 1.0, 0.05) var volume: float = 0.8
@export_range(1, 10, 1) var enemy_count: int = 5
```

Format: `@export_range(min, max, step)`

---

## @export with Enum

Show a dropdown in the Inspector:

```gdscript
enum State { IDLE, RUNNING, JUMPING, FALLING }

@export var initial_state: State = State.IDLE
```

---

## @onready

Initializes a variable **after** the node enters the tree. Use when you need child node references.

```gdscript
extends CharacterBody2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D
@onready var animation: AnimationPlayer = $AnimationPlayer
```

### @onready vs @export

| | `@onready` | `@export` |
|---|-----------|-----------|
| **Value source** | Child node path | Inspector value |
| **Use for** | Node references | Configurable parameters |
| **Set by** | Engine (auto) | Developer (Inspector) |
| **Example** | `@onready var sprite = $Sprite2D` | `@export var speed: float = 200.0` |

---

## Combining Both

```gdscript
extends CharacterBody2D

# Inspector-configurable
@export var speed: float = 200.0
@export var max_health: int = 100
@export_range(0, 100) var health: int = 100

# Node references (set by engine)
@onready var sprite: Sprite2D = $Sprite2D
@onready var hit_sound: AudioStreamPlayer2D = $HitSound

func take_damage(amount: int) -> void:
    health -= amount
    health = clamp(health, 0, max_health)
    hit_sound.play()
    if health <= 0:
        sprite.modulate = Color.RED
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `export var` without `@` | Silently ignored as comment | Use `@export var` |
| `@onready` for non-child nodes | Null reference crash | `@onready` only works for child nodes |
| Forgetting type hint | Generic Inspector field | Always add `: Type` after variable name |
| Using `@onready` for Inspector values | Can't edit in Inspector | Use `@export` for configurable values |
| `@onready var x = $Path/To/Node` with wrong path | Null reference at runtime | Verify node path exists in scene tree |
