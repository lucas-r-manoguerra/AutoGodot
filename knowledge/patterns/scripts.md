---
type: Reference
title: GDScript Patterns
description: Reusable patterns for Godot 4.x game development including health, movement, spawn, and signals
tags:
  - gdscript
  - patterns
  - health
  - movement
  - signals
  - spawn
  - character-body
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-24T15:00:00Z"
---

# GDScript Patterns

Reusable patterns for Godot 4.x game development.

## 1. Health/Damage System

**Problem:** Need health tracking with damage, healing, and death events.

**Solution:** A `take_damage()` / `heal()` pair with signal emission on every change.

```gdscript
extends CharacterBody2D

signal health_changed(new_health: int)
signal died

@export var health: int = 100
var max_health: int = 100

func take_damage(amount: int) -> bool:
	health -= amount
	health = clamp(health, 0, max_health)
	health_changed.emit(health)
	if health <= 0:
		died.emit()
		return true
	return false

func heal(amount: int):
	health += amount
	health = clamp(health, 0, max_health)
	health_changed.emit(health)
```

**Gotchas:**
- Always `clamp(health, 0, max_health)` — never let it go negative or above max.
- Emit the signal on every change so the UI can react, not only on death.
- `take_damage` returns `true` when the entity dies — callers can use that to trigger animations or scoring before `queue_free()`.

---

## 2. Top-Down Movement (WASD)

**Problem:** Need 4-directional movement from player input.

**Solution:** `Input.get_vector()` or per-action checks mapped to `self.velocity`, then `move_and_slide()` with no arguments.

```gdscript
extends CharacterBody2D

@export var speed: float = 300.0

func _physics_process(_delta: float):
	var input_dir = Vector2.ZERO
	if Input.is_action_pressed("move_up"):
		input_dir.y -= 1
	if Input.is_action_pressed("move_down"):
		input_dir.y += 1
	if Input.is_action_pressed("move_left"):
		input_dir.x -= 1
	if Input.is_action_pressed("move_right"):
		input_dir.x += 1
	velocity = input_dir.normalized() * speed
	move_and_slide()
```

**Gotchas:**
- Always assign to `self.velocity` (inherited from `CharacterBody2D`), never create a local variable and pass it to `move_and_slide()`.
- `move_and_slide()` takes **no arguments** in Godot 4.x. Passing velocity was Godot 3.x API.
- Normalize the input vector so diagonal movement is the same speed as cardinal movement.
- Use `_physics_process`, not `_process` — movement must be tied to the physics tick.

---

## 3. Platformer Movement (Gravity + Jump)

**Problem:** Need a character that falls with gravity and jumps when a button is pressed.

**Solution:** Accumulate `velocity.y` from gravity each frame, apply jump impulse on button press.

```gdscript
extends CharacterBody2D

const SPEED = 200.0
const JUMP_VELOCITY = -400.0

var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")

func _physics_process(delta: float):
	if not is_on_floor():
		velocity.y += gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	var direction = Input.get_axis("move_left", "move_right")
	velocity.x = direction * SPEED

	move_and_slide()
```

**Gotchas:**
- Read gravity from `ProjectSettings` so it stays in sync with the project's physics settings.
- Check `is_on_floor()` before allowing a jump — prevents mid-air double jumps.
- Negative Y is **up** in Godot 2D. Jump velocity must be negative.
- `Input.get_axis(negative_action, positive_action)` returns a float from -1 to 1 — clean and compact for horizontal movement.

---

## 4. Spawn System

**Problem:** Need to spawn entities at intervals with random positions.

**Solution:** A `Timer` node with `timeout` signal connected in `_ready()`. The callback instantiates the scene and adds it to the tree.

```gdscript
extends Node2D

@export var enemy_scene: PackedScene

func _ready():
	$SpawnTimer.timeout.connect(_on_spawn_timer_timeout)

func spawn_enemy():
	if enemy_scene == null:
		return
	var enemy = enemy_scene.instantiate()
	enemy.global_position = Vector2(randf_range(100, 1180), randf_range(100, 620))
	enemy.enemy_died.connect(_on_enemy_died)
	add_child(enemy)

func _on_spawn_timer_timeout():
	spawn_enemy()
```

**Gotchas:**
- Use `$SpawnTimer.wait_time` (set in the editor) rather than manual delta accumulation — the engine handles drift and pause.
- Always null-check `PackedScene` exports before calling `.instantiate()`.
- Connect the spawned entity's signals **after** instantiation but **before** `add_child()` — signal handlers may fire immediately on add.

---

## 5. Signal Wiring

**Problem:** Need nodes to communicate without tight coupling.

**Solution:** Declare custom signals, connect them in `_ready()`, and emit with `.emit()`.

```gdscript
# game_manager.gd
extends Node2D

signal game_over

func _ready():
	var player = $Player
	player.died.connect(_on_player_died)
	$SpawnTimer.timeout.connect(_on_spawn_timer_timeout)

func _on_player_died():
	game_over.emit()
	print("Game Over!")

func _on_spawn_timer_timeout():
	spawn_enemy()
```

**Gotchas:**
- Always connect signals in `_ready()`, never in `_process()` — repeated connections cause duplicate callbacks.
- Use the Godot 4.x syntax: `signal_name.connect(method)`. The old `connect("signal_name", object, "method")` is Godot 3.x API.
- If a node might be freed before the signal fires, use `CONNECT_ONE_SHOT` flag or disconnect in the node's exit tree.
- You can pass arguments through signals: `signal enemy_died(points: int)` → `enemy_died.emit(100)` → callback receives `points`.

---

## Related

- [migration/godot-4.md](../migration/godot-4.md) - API changes for move_and_slide, signals, and exports
- [checklists/character-scene.md](../checklists/character-scene.md) - Required nodes for character scenes
- [reference/node-paths.md](../reference/node-paths.md) - Node referencing with $ and get_node()
