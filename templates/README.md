# AutoGodot Templates

Cheat sheets for common Godot 4.7 patterns. AI agents should load the relevant
template before writing code to avoid well-known pitfalls.

## Template Index

| Template | Description |
|----------|-------------|
| [godot-4-migration.md](godot-4-migration.md) | Godot 3.x to 4.x API migration reference |
| `gdscript-patterns.md` | GDScript idioms, signals, state machines *(planned)* |
| `scene-structure.md` | Node hierarchy and scene composition *(planned)* |
| `physics-collision.md` | Collision layers, masks, and bodies *(planned)* |
| `ui-layout.md` | Control nodes, anchors, and responsive UI *(planned)* |
| `resource-loading.md` | PackedScene, preload, and resource management *(planned)* |
| `exported-vars.md` | @export, @onready, and Inspector integration *(planned)* |

## When to Use Each

| Situation | Template to load |
|-----------|-----------------|
| Porting a Godot 3.x project or script | `godot-4-migration.md` |
| Writing GDScript with signals and state machines | `gdscript-patterns.md` |
| Building a new scene tree from scratch | `scene-structure.md` |
| Working with CharacterBody2D or RigidBody2D | `physics-collision.md` |
| Creating HUD, menus, or responsive layouts | `ui-layout.md` |
| Instantiating scenes or loading assets at runtime | `resource-loading.md` |
| Exposing variables to the Inspector | `exported-vars.md` |

## Top 5 Mistakes Agents Make

1. **Old signal syntax** — Using `connect("signal", obj, "method")` instead of
   `signal_name.connect(method)`. Causes immediate parse errors in 4.x.

2. **move_and_slide with velocity arg** — Writing `move_and_slide(velocity)` when
   4.x expects `self.velocity = velocity; move_and_slide()`.

3. **Missing @export** — Writing `export var` without the `@` prefix. The old
   syntax is silently ignored as a comment.

4. **yield instead of await** — Using `yield(obj, "signal")` which no longer
   compiles. Replace with `await signal_name`.

5. **PhysicsServer name swap** — Referencing `Physics2DServer` which was renamed
   to `PhysicsServer2D` in 4.x. Causes "not found" errors at runtime.

## Usage for AI Agents

Load templates as context before generating Godot code:

```
# Before writing code, read the relevant template:
read templates/godot-4-migration.md

# Then generate Godot 4.7 code using the patterns from the template.
```

Always verify generated code against the template checklist before returning
results to the user.
