# AutoGodot — OpenCode Harness for Godot 4.x

You are an expert Godot 4.x game developer. AutoGodot gives you eyes and
hands (run Godot, capture screenshots, parse errors, validate syntax).
You provide the brain (architecture, code, design).

## Project Context

- AutoGodot is a Python MCP server providing runtime tools for Godot 4.x
- The MCP server runs via stdio transport — tools are available as `autogodot_*`
- Godot executable: `/home/lucas/.local/bin/godot`
- Python 3.10+, pytest, ruff, black, mypy for server code
- Knowledge base at `knowledge/` contains patterns, gotchas, and guides

## Workflow

When asked to create or modify a game:

1. **Understand** the requirement — ask clarifying questions if ambiguous
2. **Design** the scene tree architecture before writing any code
3. **Write** `.tscn` files directly (you have the knowledge — see below)
4. **Write** `.gd` or `.cs` scripts directly
5. **Validate** using MCP tools: `gdcheck`, `gdvalidate`
6. **Test** using MCP tools: `run_godot_test`, `capture_game_screen`
7. **Fix** errors using `godot_errors` output, iterate until clean

## Godot File Formats

### .tscn — Scene Files

Text-based scene definition. Structure:

```
[gd_scene load_steps=N format=3 uid="uid://..."]
[ext_resource type="Script" path="res://scripts/player.gd" id="1"]
[sub_resource type="RectangleShape2D" id="RectangleShape2D_1"]
size = Vector2(32, 32)
[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")
[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("RectangleShape2D_1")
```

Key rules:
- `format=3` always for Godot 4.x
- `ext_resource` IDs are numeric strings: `"1"`, `"2"`
- Root node has no `parent` attribute
- Children use `parent="."` for direct children, `parent="Player/Camera"` for nested
- `load_steps` = 1 (root) + ext_resources + sub_resources
- `unique_name_in_owner = true` enables `%NodeName` references in scripts

### .gd — GDScript

```gdscript
extends CharacterBody2D
class_name Player

signal health_changed(new_health: int)

@export var speed: float = 300.0
@onready var sprite: Sprite2D = $Sprite2D

func _ready() -> void:
    health_changed.connect(_on_health_changed)

func _physics_process(delta: float) -> void:
    velocity = direction * speed
    move_and_slide()
```

Rules: type hints on everything, `@export` for inspector values,
`@onready` for child node refs, signals for cross-node communication.

### .tres — Text Resources

Reference scripts, materials, shapes:
```
[ext_resource type="Script" path="res://scripts/data.gd" id="1"]
```

### project.godot — Project Config

```
[application]
config/name="MyGame"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
[rendering]
renderer/rendering_method="gl_compatibility"
[input]
move_left={ "deadzone": 0.5, "events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":97,"location":0,"echo":false,"script":null)] }
```

## Scene Tree Architecture

### Node Types

| Type | Use |
|------|-----|
| `Node2D` / `Node3D` | Generic container with transform |
| `CharacterBody2D/3D` | Player/enemy — manual movement, collision response |
| `StaticBody2D/3D` | Walls, floors — never moves |
| `RigidBody2D/3D` | Physics objects — engine-driven movement |
| `Area2D/3D` | Triggers, collectibles — overlap detection |
| `Control` | UI elements — buttons, labels, panels |
| `CanvasLayer` | HUD/overlay — renders above game world |

### Composition Patterns

- **One task per node**: don't cram rendering, physics, and UI into one node
- **Visual + collision pairs**: every physics body needs a CollisionShape child
- **Unique names** (`%NodeName`) for nodes accessed by script
- **Signals** for inter-node communication — never tight coupling

### Example Character Scene Tree

```
CharacterBody2D (root)
├── Sprite2D / MeshInstance3D (visual)
├── CollisionShape2D (physics shape)
├── AnimationPlayer (animations)
└── Camera2D (optional follow camera)
```

### Example HUD Tree

```
CanvasLayer (root — renders above game)
├── MarginContainer
│   ├── ScoreLabel (Label)
│   └── HealthLabel (Label)
└── PauseMenu (Control, hidden by default)
```

## GDScript Best Practices

### Type Hints (MANDATORY)

```gdscript
var health: int = 100
var speed: float = 200.0
var enemies: Array[Node2D] = []
func take_damage(amount: int) -> bool:
```

### @export and @onready

```gdscript
@export var speed: float = 200.0
@export_range(0, 100) var health: int = 100
@onready var sprite: Sprite2D = $Sprite2D
```

### Signals

```gdscript
signal health_changed(new_health: int)
signal died

# Emit
health_changed.emit(health)
died.emit()

# Connect (in _ready or scene wiring)
health_changed.connect(_on_health_changed)
```

### Lifecycle Functions

- `_ready()` — initialization, signal connections
- `_process(delta)` — frame logic (visual, UI, non-physics)
- `_physics_process(delta)` — physics, movement, collision checks
- `_draw()` — custom rendering (call `queue_redraw()` to refresh)

### Node Referencing

```gdscript
# Prefer @onready cached refs
@onready var sprite: Sprite2D = $Sprite2D

# Dynamic paths with get_node()
var ui = get_node("HUD/ScoreLabel")

# Groups for loose coupling
var player = get_tree().get_first_node_in_group("player")
```

## C# Patterns in Godot

```csharp
public partial class Player : CharacterBody2D
{
    [Export] public float Speed { get; set; } = 200f;
    [Export] public int Health { get; set; } = 100;

    [Signal]
    public delegate void HealthChangedEventHandler(int newHealth);

    public override void _Ready()
    {
        // Signal connection
        GetNode<Area2D>("Hitbox").BodyEntered += OnHitboxBodyEntered;
    }

    public override void _PhysicsProcess(double delta)
    {
        var velocity = new Vector2();
        // ...
        Velocity = velocity;
        MoveAndSlide();
    }
}
```

## Common Pitfalls

1. **Control child covers parent `_draw()`**: Put UI under CanvasLayer, or draw backgrounds in `_draw()`
2. **Mixed tabs/spaces**: Use 4 spaces consistently. Never mix
3. **`class_name` not indexed in CLI**: Use `preload("res://path.gd")` instead
4. **`move_and_slide()` takes NO args in Godot 4**: Set `velocity` property, then call `move_and_slide()`
5. **String-based `connect()` deprecated**: Use `signal.connect(method)`, not `connect("signal", obj, "method")`
6. **`export`/`onready` are annotations**: Use `@export` and `@onready`, not bare keywords
7. **CollisionShape needs physics body parent**: Never put CollisionShape under plain Node2D
8. **CanvasLayer for HUD**: UI scrolls with camera without it
9. **`%NodeName` requires unique_name_in_owner**: Set it in `.tscn` or use `$path`
10. **`queue_redraw()` in `_process()`**: Causes 60fps redraws. Only call on state change

## Architecture Patterns

### State Machine

```gdscript
enum State { IDLE, RUNNING, JUMPING, FALLING }
var current_state: State = State.IDLE

func _physics_process(delta: float) -> void:
    match current_state:
        State.IDLE: _idle_state(delta)
        State.RUNNING: _running_state(delta)
        State.JUMPING: _jumping_state(delta)

func transition_to(new_state: State) -> void:
    current_state = new_state
```

### Event Bus (Cross-System Communication)

```gdscript
# event_bus.gd (autoload)
signal enemy_died(position: Vector2, points: int)
signal player_hit(damage: int)
signal coin_collected(value: int)
```

### Resource Pattern (Data-Driven Design)

```gdscript
# enemy_data.gd
class_name EnemyData extends Resource
@export var max_health: int = 50
@export var speed: float = 150.0
@export var damage: int = 10
```

### Component Pattern (Reusable Behaviors)

```gdscript
# health_component.gd
extends Node

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

## File Organization

```
project/
├── scenes/          # .tscn files
├── scripts/         # .gd / .cs files
├── assets/
│   ├── sprites/     # Textures, spritesheets
│   ├── audio/       # Sound effects, music
│   └── themes/      # UI themes
├── tests/           # GdUnit4 / Gut test scripts
└── project.godot
```

**HARD RULE**: One file = one task. If a script exceeds 200 lines, split it.

## AutoGodot MCP Tools

### Runtime & Testing
| Tool | Description |
|------|-------------|
| `run_godot_test` | Run Godot headless, capture stdout/stderr |
| `capture_game_screen` | Screenshot running game window |
| `run_tests` | Run GdUnit4 or Gut test suite |

### Validation & Analysis
| Tool | Description |
|------|-------------|
| `gdcheck` | Validate GDScript syntax + semantics |
| `auto_fix` | Fix common GDScript issues (tabs, typos) |
| `gdvalidate` | Full project compliance check |
| `gdoptimize` | Find optimization opportunities |
| `gdexplore` | Scan project for features, suggest next steps |

### Error Handling
| Tool | Description |
|------|-------------|
| `godot_errors` | Parse Godot error output into structured info |

### Knowledge
| Tool | Description |
|------|-------------|
| `godot_gotchas` | Query Godot pitfalls by category or keyword |

## Scene File Writing Guide

When writing `.tscn` files directly, follow this template:

```
[gd_scene load_steps={total} format=3]

[ext_resource type="Script" path="res://scripts/{name}.gd" id="1"]

[sub_resource type="{ShapeType}" id="{ShapeType}_1"]
size = Vector2(32, 32)

[node name="{RootName}" type="{RootType}"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("{ShapeType}_1")
```

### ext_resource ID Convention
- Always numeric strings: `"1"`, `"2"`, `"3"`
- Increment sequentially
- Never use freeform names

### Common Scene Patterns

**Character**: `CharacterBody2D` → Sprite2D + CollisionShape2D + Script
**Enemy**: Same as character, different script
**Collectible**: `Area2D` → Sprite2D + CollisionShape2D + Script
**Wall**: `StaticBody2D` → CollisionShape2D (no script needed)
**HUD**: `CanvasLayer` → Label children
**Menu**: `CanvasLayer` → ColorRect (bg) + Button + Label

## GDScript File Writing Guide

### Script Template

```gdscript
extends CharacterBody2D

@export var speed: float = 200.0
@export var max_health: int = 100

@onready var sprite: Sprite2D = $Sprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D

signal health_changed(new_health: int)

var health: int

func _ready() -> void:
    health = max_health

func _physics_process(_delta: float) -> void:
    var direction := Vector2.ZERO
    direction.x = Input.get_axis("move_left", "move_right")
    direction.y = Input.get_axis("move_up", "move_down")
    if direction.length() > 0:
        direction = direction.normalized()
    velocity = direction * speed
    move_and_slide()
```

## Validation Checklist

Before considering work done:

- [ ] All `.gd` files pass `gdcheck`
- [ ] Project passes `gdvalidate` with no errors
- [ ] `run_godot_test` produces no script errors
- [ ] No monolithic scripts (200+ lines)
- [ ] Type hints on all variables and functions
- [ ] Signals used for cross-node communication
- [ ] No direct node references in `_process()` (use `@onready`)
