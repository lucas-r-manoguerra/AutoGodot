# Exploration: Godot Templates & API Reference for AutoGodot MCP

## Current State

### What Exists

AutoGodot has a working MCP server with 9 tools:

| Tool | Module | Structured? | Status |
|------|--------|:-----------:|:------:|
| `write_game_file` | mcp_server.py | Raw text | ✅ Working |
| `run_godot_test` | godot_controller.py | N/A | ✅ Working |
| `capture_game_screen` | vision_qa.py | N/A | ✅ Working |
| `read_scene` | scene_builder.py | ✅ JSON | ✅ Working |
| `create_scene` | scene_builder.py | ✅ JSON | ✅ Working |
| `modify_scene` | scene_builder.py | ✅ JSON | ✅ Working |
| `read_script` | script_builder.py | ✅ JSON | ✅ Working |
| `create_script` | script_builder.py | ✅ JSON | ✅ Working |
| `modify_script` | script_builder.py | ✅ JSON | ✅ Working |

The `ScriptBuilder` supports: extends, class_name, signals, variables (@export + regular), functions (with body), and surgical modifications. The `SceneBuilder` supports: ext_resources, sub_resources, node trees, property setting, and signal connections via `godot-parser`.

### What the test_project Demonstrates

The test_project is a complete working game with:
- **Player** (CharacterBody2D): top-down movement, health/damage signals, Polygon2D visual
- **Enemy** (CharacterBody2D): chase AI, death signal, Polygon2D visual (pentagon)
- **GameManager** (Node2D): spawn system, score tracking, signal wiring
- **GameUI** (CanvasLayer): score/health labels
- **Main scene**: composes all of the above with connections

### Recurring Problems Identified

1. **ScriptBuilder `$` node reference bug**: `$GameUI` in function body lines gets dropped when passed through JSON definition. Workaround: use `\$` or raw heredoc via `write_game_file`.

2. **Godot 4.x API knowledge gaps**: Agents use `move_and_slide(velocity)` (Godot 3.x API) instead of `self.velocity = v; move_and_slide()` (Godot 4.x). This pattern is NOT in any template or reference.

3. **Scenes without visual nodes**: CharacterBody2D scenes created with only CollisionShape2D, no Sprite2D/Polygon2D. Agents don't know that physics bodies need visual representation.

4. **ext_resource ID mismatch**: `godot-parser` auto-numbers ext_resources (1, 2, 3) but property values may reference string IDs ("player_script"), causing broken .tscn files. The test_project's manually-written .tscn files use numeric IDs and work correctly.

5. **No common pattern references**: Agents invent spawn systems, health systems, signal wiring from scratch each time, leading to inconsistent or incorrect implementations.

---

## Affected Areas

- `core/script_builder.py` — The `$` bug in `_gen_func_body()` drops `$` from node references in body lines
- `core/scene_builder.py` — `add_ext_resource()` doesn't let callers control the ID; godot-parser auto-numbers
- `test_project/` — Already has working examples that could serve as template sources
- **NEW** `templates/` directory — Proposed location for Godot 4.7 pattern templates
- **NEW** `docs/godot-api-reference.md` — Proposed API reference for AI agents

---

## Template Categories & Contents

### Category 1: Character Scenes (HIGH PRIORITY)

**Why**: Most common scene type. Agents consistently forget visual nodes and use wrong APIs.

**Templates needed:**

| Template | Root Type | Required Children | Key Scripts |
|----------|-----------|-------------------|-------------|
| `player_topdown.tscn` | CharacterBody2D | Polygon2D, CollisionShape2D | movement, health, damage |
| `player_platformer.tscn` | CharacterBody2D | Polygon2D, CollisionShape2D, RayCast2D (floor) | jump, gravity, movement |
| `enemy_melee.tscn` | CharacterBody2D | Polygon2D, CollisionShape2D, Area2D (attack range) | chase, attack, health |
| `enemy_ranged.tscn` | CharacterBody2D | Polygon2D, CollisionShape2D, Marker2D (muzzle) | patrol, shoot, health |
| `npc_static.tscn` | CharacterBody2D | Polygon2D, CollisionShape2D | dialog trigger |
| `pickup_item.tscn` | Area2D | Sprite2D/Polygon2D, CollisionShape2D | collect, respawn |

**Critical pattern for each**:
- MUST have visual node (Polygon2D or Sprite2D) — agents always forget this
- MUST have CollisionShape2D with sub_resource shape
- script = ExtResource("1") must reference correct ext_resource ID

**Reference files**: `test_project/scenes/player.tscn`, `test_project/scenes/enemy.tscn`

### Category 2: Scene Structure Patterns (HIGH PRIORITY)

**Why**: Agents create scenes with wrong node hierarchy, missing resources, or broken references.

**Patterns:**

1. **Minimal CharacterBody2D scene** (the "always include these nodes" checklist):
   ```
   Root (CharacterBody2D) → script
     ├─ VisualNode (Polygon2D or Sprite2D)
     └─ CollisionShape2D → SubResource(shape)
   ```

2. **Game level scene** (root + UI + spawners):
   ```
   Main (Node2D) → script
     ├─ Background (ColorRect)
     ├─ Enemies (Node2D) — container for spawned enemies
     ├─ UI (CanvasLayer) → script
     │   ├─ ScoreLabel (Label)
     │   └─ HealthLabel (Label)
     └─ SpawnTimer (Timer)
   ```

3. **HUD overlay scene** (reusable UI):
   ```
   HUD (CanvasLayer)
     ├─ MarginContainer
     │   ├─ HBoxContainer
     │   │   ├─ HealthBar (ProgressBar)
     │   │   └─ ScoreLabel (Label)
     └─ PauseMenu (VBoxContainer, hidden)
   ```

**ext_resource ID convention**: Use simple numeric strings: `"1"`, `"2"`, `"3"`. Never use descriptive strings like `"player_script"`. The godot-parser auto-numbers match this.

### Category 3: Script Patterns (HIGH PRIORITY)

**Why**: Common game systems agents need to implement. Without references, they invent incorrect versions.

**Templates:**

1. **Health/Damage system** (from `test_project/scripts/player.gd`):
   ```gdscript
   # Signals
   signal health_changed(new_health: int)
   signal died

   # Vars
   @export var max_health: int = 100
   var health: int

   func _ready():
       health = max_health

   func take_damage(amount: int) -> bool:
       health = clamp(health - amount, 0, max_health)
       health_changed.emit(health)
       if health <= 0:
           died.emit()
           return true
       return false

   func heal(amount: int):
       health = clamp(health + amount, 0, max_health)
       health_changed.emit(health)
   ```

2. **Top-down movement** (GODOT 4.x CORRECT API):
   ```gdscript
   # CRITICAL: Godot 4.x move_and_slide() takes NO arguments
   # Set self.velocity BEFORE calling move_and_slide()
   func _physics_process(_delta: float):
       var input_dir = Vector2.ZERO
       input_dir.x = Input.get_axis("move_left", "move_right")
       input_dir.y = Input.get_axis("move_up", "move_down")
       velocity = input_dir.normalized() * speed
       move_and_slide()  # NO arguments!
   ```

3. **Platformer movement** (GODOT 4.x):
   ```gdscript
   func _physics_process(delta: float):
       # Apply gravity
       if not is_on_floor():
           velocity.y += gravity * delta

       # Jump
       if Input.is_action_just_pressed("jump") and is_on_floor():
           velocity.y = -jump_speed

       # Horizontal movement
       velocity.x = Input.get_axis("move_left", "move_right") * speed
       move_and_slide()  # NO arguments!
   ```

4. **Enemy chase AI** (from `test_project/scripts/enemy.gd`):
   ```gdscript
   var player: Node2D = null

   func _ready():
       player = get_tree().get_first_node_in_group("player")

   func _physics_process(_delta: float):
       if player == null:
           return
       var direction = (player.global_position - global_position).normalized()
       velocity = direction * speed
       move_and_slide()  # NO arguments!
   ```

5. **Spawn system** (from `test_project/scripts/game_manager.gd`):
   ```gdscript
   @export var enemy_scene: PackedScene
   var spawn_timer: Timer

   func _ready():
       spawn_timer = $SpawnTimer
       spawn_timer.timeout.connect(_on_spawn_timer_timeout)

   func spawn_enemy():
       if enemy_scene == null:
           return
       var enemy = enemy_scene.instantiate()
       enemy.global_position = Vector2(randf_range(100, 1180), randf_range(100, 620))
       enemy.enemy_died.connect(_on_enemy_died)
       add_child(enemy)
   ```

6. **Signal wiring pattern** (from test_project):
   ```gdscript
   # In parent script _ready():
   func _ready():
       $Player.died.connect(_on_player_died)
       $SpawnTimer.timeout.connect(_on_spawn_timer_timeout)

   func _on_player_died():
       game_over.emit()

   func _on_enemy_died(points: int):
       score += points
       $UI.update_score(score)
   ```

### Category 4: Movement Patterns (MEDIUM PRIORITY)

**Why**: Movement is the #1 thing agents get wrong due to Godot 3→4 API changes.

**Key API differences (Godot 3.x → 4.x):**

| Feature | Godot 3.x (WRONG) | Godot 4.x (CORRECT) |
|---------|-------------------|---------------------|
| CharacterBody2D movement | `move_and_slide(velocity)` | `self.velocity = v; move_and_slide()` |
| CharacterBody2D velocity | Local var `velocity` | Property `self.velocity` |
| move_and_slide floor detection | `is_on_floor()` (same) | `is_on_floor()` (same) |
| get_axis | `Input.get_axis()` (same) | `Input.get_axis()` (same) |
| KinematicBody2D | `extends KinematicBody2D` | `extends CharacterBody2D` |
| RigidBody2D physics | Manual `move_and_slide` | Use `_integrate_forces` or `apply_central_impulse` |

**Movement templates:**
- Top-down 8-directional
- Top-down 4-directional (grid-aligned)
- Platformer (left/right + jump)
- Platformer with wall jump
- Follow camera (Camera2D following player)
- Area2D-based movement (enemies that patrol waypoints)

### Category 5: UI Patterns (MEDIUM PRIORITY)

**Why**: UI is the second most common failure — agents create UI nodes without proper layout containers.

**Patterns:**

1. **HUD with CanvasLayer** (from test_project):
   ```
   CanvasLayer
     ├─ Label (ScoreLabel) — positioned with offset_*
     └─ Label (HealthLabel) — positioned with offset_*
   ```

2. **HUD with proper layout** (recommended):
   ```
   CanvasLayer
     └─ MarginContainer (anchors: full rect)
       └─ VBoxContainer
         ├─ HBoxContainer
         │   ├─ HealthBar (ProgressBar)
         │   └─ ScoreLabel (Label)
         └─ (spacer)
   ```

3. **Pause menu**:
   ```
   PauseMenu (CanvasLayer, visible=false)
     └─ ColorRect (semi-transparent bg)
       └─ VBoxContainer (centered)
         ├─ ResumeButton (Button)
         ├─ RestartButton (Button)
         └─ QuitButton (Button)
   ```

4. **Health bar** (ProgressBar pattern):
   ```
   HealthBar (ProgressBar)
     - min_value = 0
     - max_value = 100
     - value = 100
     - show_percentage = false
   ```

### Category 6: Scene Connections (LOW PRIORITY)

**Why**: Signal wiring is straightforward but agents often forget or misname methods.

**Common connections:**
- `Button.pressed` → handler method
- `Timer.timeout` → handler method
- `Area2D.area_entered` → handler method
- Custom signals (e.g., `died`, `health_changed`) → parent handler

---

## Recommended Godot 4.7 API Reference Topics

### 1. Node Types & When to Use Them

| Node Type | Use Case | Key Properties |
|-----------|----------|----------------|
| `Node2D` | 2D game root, containers | `position`, `rotation`, `scale` |
| `CharacterBody2D` | Player/enemy with physics | `velocity`, `move_and_slide()`, `is_on_floor()` |
| `Area2D` | Triggers, pickups, hitboxes | `area_entered`, `body_entered` signals |
| `RigidBody2D` | Physics objects (balls, debris) | `apply_central_impulse()`, `gravity_scale` |
| `StaticBody2D` | Walls, platforms (immovable) | Needs CollisionShape2D |
| `CanvasLayer` | UI overlays | `layer` property |
| `Control` | UI base class | `anchors`, `offsets`, `size_flags` |
| `Label` | Text display | `text`, `horizontal_alignment` |
| `Button` | Interactive UI | `pressed` signal, `text` |
| `ProgressBar` | Health bars, loading | `min_value`, `max_value`, `value` |
| `Timer` | Delayed/repeated actions | `wait_time`, `autostart`, `timeout` signal |
| `Marker2D` | Position markers (muzzle, spawn) | `position` only |
| `Camera2D` | Viewport camera | `zoom`, `position_smoothing` |
| `PackedScene` | Preloaded scene resource | `.instantiate()` to create instance |

### 2. Movement API (Godot 4.x)

```gdscript
# CharacterBody2D — THE correct way
func _physics_process(delta: float) -> void:
    # Set velocity property directly
    velocity.x = Input.get_axis("left", "right") * speed
    velocity.y += gravity * delta  # For platformers
    move_and_slide()  # Takes NO arguments in Godot 4.x!

# Checking collisions after move_and_slide
if is_on_floor():
    pass  # On ground
if is_on_wall():
    pass  # Hit a wall
if is_on_ceiling():
    pass  # Hit ceiling

# Getting collision info
for i in get_slide_collision_count():
    var collision = get_slide_collision(i)
    var collider = collision.get_collider()
```

### 3. Signal API (Godot 4.x)

```gdscript
# Defining signals
signal died
signal health_changed(new_health: int)

# Emitting
died.emit()
health_changed.emit(health)

# Connecting (in code)
$Player.died.connect(_on_player_died)
$Button.pressed.connect(_on_button_pressed)
$Timer.timeout.connect(_on_timer_timeout)

# Disconnecting
$Player.died.disconnect(_on_player_died)

# One-shot connection
$Player.died.connect(_on_player_died, CONNECT_ONE_SHOT)

# Lambda connection
$Button.pressed.connect(func(): print("pressed"))
```

### 4. Scene Instantiation

```gdscript
# Preloading (at top of script)
const EnemyScene = preload("res://scenes/enemy.tscn")

# Loading (at runtime)
var EnemyScene = load("res://scenes/enemy.tscn")

# Instantiating
var enemy = EnemyScene.instantiate()
enemy.global_position = Vector2(100, 200)
add_child(enemy)

# Adding to group (for finding later)
enemy.add_to_group("enemies")

# Finding nodes by group
var player = get_tree().get_first_node_in_group("player")
var enemies = get_tree().get_nodes_in_group("enemies")
```

### 5. Input Map Setup (project.godot)

```ini
[input]
move_up={
"deadzone": 0.5,
"events": [Object(InputEventKey,...,"physical_keycode":87,...)]
}
```

Physical keycodes: W=87, A=65, S=83, D=68, Space=32, Enter=4194309

### 6. Common Gotchas for AI Agents

| Gotcha | Wrong | Correct |
|--------|-------|---------|
| move_and_slide args | `move_and_slide(velocity)` | `self.velocity = v; move_and_slide()` |
| Visual nodes | CollisionShape2D only | Add Polygon2D or Sprite2D |
| ext_resource IDs | `"player_script"` | `"1"`, `"2"` (numeric) |
| Node access | `$Player` in body | Works, but `$` drops in JSON body lines |
| Groups | Not using groups | Use `add_to_group("name")` for lookup |
| CanvasLayer | Labels directly in Node2D | Labels MUST be in CanvasLayer for UI |
| PackedScene | `enemy_scene.instantiate()` | Check `if enemy_scene != null` first |
| Timer | Manual `_process` timing | Use Timer node with `timeout` signal |

---

## Existing Files as Template Sources

| File | Can Serve As |
|------|-------------|
| `test_project/scripts/player.gd` | Health system, top-down movement, signal pattern |
| `test_project/scripts/enemy.gd` | Chase AI, death signal, group lookup |
| `test_project/scripts/game_manager.gd` | Spawn system, signal wiring, score tracking |
| `test_project/scripts/game_ui.gd` | Label updates, CanvasLayer UI |
| `test_project/scenes/player.tscn` | CharacterBody2D scene with visual + collision |
| `test_project/scenes/enemy.tscn` | Enemy scene with pentagon shape |
| `test_project/scenes/main.tscn` | Game level with all components composed |
| `test_project/scenes/game_ui.tscn` | Standalone UI scene |
| `test_project/project.godot` | Input map, display settings, rendering config |

---

## Risks & Constraints

### Technical Risks

1. **`$` node reference bug**: The ScriptBuilder's `_gen_func_block()` joins body lines but the `$` prefix gets lost in JSON serialization through the MCP tool. This is a code bug in `script_builder.py`, not a template issue. The fix is in the builder, not the templates. Templates should document the workaround (use `\$` in JSON body lines, or use `write_game_file` for scripts with node references).

2. **ext_resource ID management**: `godot-parser`'s `add_ext_resource()` auto-assigns IDs. The current `SceneBuilder.create()` doesn't let callers control IDs. If an agent creates a scene with ext_resources and then tries to reference them in properties, the auto-numbered IDs must match. Current behavior: godot-parser uses sequential integers (1, 2, 3), which aligns with the convention. Risk is low if agents follow the numeric ID convention.

3. **Template staleness**: Godot version updates may change APIs. Templates need version pinning (e.g., "Godot 4.7" header).

### Design Constraints

4. **Templates as documentation, not code**: Templates should be reference documents (markdown with code blocks), not executable files. The MCP tools generate code from JSON definitions — templates show the *target output*, not the input format.

5. **Scope boundary**: Templates cover patterns and API reference. They do NOT fix the `$` bug or the ext_resource ID issue — those are code changes.

6. **Agent context window**: API reference must be concise. Agents have limited context; verbose references reduce the budget for actual implementation. Keep the reference to "what changed from 3.x" and "common gotchas" rather than full API docs.

---

## Recommended Implementation Order

### Phase 1: Critical Templates (blocks most agent errors)

1. **`templates/README.md`** — Index of all templates, quick-reference table
2. **`templates/godot-4-migration.md`** — Godot 3→4 API changes (move_and_slide, etc.)
3. **`templates/character-scene-checklist.md`** — "Always include these nodes" checklist
4. **`templates/script-patterns.md`** — Health, movement, spawn, signal patterns

### Phase 2: Scene Templates (improve scene creation quality)

5. **`templates/scene-structures.md`** — Common scene tree layouts
6. **`templates/ui-patterns.md`** — HUD, menus, health bars

### Phase 3: Bug Fixes (code changes, not templates)

7. Fix `$` reference bug in `script_builder.py` `_gen_func_block()`
8. Add optional ID parameter to `scene_builder.py` `add_ext_resource()`

---

## Ready for Proposal

**Yes** — the exploration is complete. The orchestrator should:

1. **Propose template creation** as a new `templates/` directory with the files listed above
2. **Scope the templates** as documentation (markdown), not executable code
3. **Include the Godot 4.x API reference** as a focused "gotchas" document, not full API docs
4. **Separate code fixes** ($ bug, ext_resource IDs) into a separate change proposal
5. **Use the test_project files** as the authoritative source for template content — these are known-working patterns
