# AutoGodot Templates

Cheat sheets for common Godot 4.7 patterns. AI agents should load the relevant
template before writing code to avoid well-known pitfalls.

## Template Index

| Template | Description |
|----------|-------------|
| [godot-4-migration.md](godot-4-migration.md) | Godot 3.x → 4.x API migration reference |
| [script-patterns.md](script-patterns.md) | GDScript idioms: health, movement, spawn, signals |
| [scene-structures.md](scene-structures.md) | `.tscn` file anatomy and ext_resource patterns |
| [character-scene-checklist.md](character-scene-checklist.md) | Mandatory nodes for character scenes |
| [physics-collision.md](physics-collision.md) | Collision layers, masks, and body types |
| [ui-patterns.md](ui-patterns.md) | CanvasLayer, HUD layout, menus |
| [resource-loading.md](resource-loading.md) | PackedScene, preload/load, .tres resources |
| [exported-vars.md](exported-vars.md) | @export, @onready, Inspector integration |
| [input-mapping.md](input-mapping.md) | Input Actions setup and reading input |
| [node-paths.md](node-paths.md) | $, get_node(), groups, path conventions |
| [project-structure.md](project-structure.md) | Folder layout, naming, scalability |

## When to Use Each

| Situation | Template to load |
|-----------|-----------------|
| Porting a Godot 3.x project or script | `godot-4-migration.md` |
| Writing GDScript with signals and state machines | `script-patterns.md` |
| Building a new `.tscn` file from scratch | `scene-structures.md` |
| Creating a character scene (player, enemy, NPC) | `character-scene-checklist.md` |
| Setting up collision layers and masks | `physics-collision.md` |
| Creating HUD, menus, or responsive layouts | `ui-patterns.md` |
| Instantiating scenes or loading assets at runtime | `resource-loading.md` |
| Exposing variables to the Inspector | `exported-vars.md` |
| Configuring keyboard/gamepad input | `input-mapping.md` |
| Referencing nodes with $ or get_node() | `node-paths.md` |
| Organizing project folders for scalability | `project-structure.md` |

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
