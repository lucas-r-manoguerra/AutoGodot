---
type: Index
title: AutoGodot Knowledge Bundle
description: Godot 4.7 patterns, references, checklists, and migration guides for AI agents
status: stable
generated:
  by: autogodot-agent
  at: "2026-07-24T15:00:00Z"
---

# AutoGodot Knowledge Bundle

Cheat sheets for common Godot 4.7 patterns. AI agents should load the relevant
concept before writing code to avoid well-known pitfalls.

## Categories

* [Migration](migration/index.md) - Godot 3.x to 4.x API migration reference
* [Patterns](patterns/index.md) - GDScript idioms: health, movement, spawn, signals, UI, resource loading, input
* [Checklists](checklists/index.md) - Mandatory node checklists for character scenes and project organization
* [Reference](reference/index.md) - Physics, collision, exports, and node path conventions
* [Scene](scene/index.md) - .tscn file anatomy and ext_resource patterns

## When to Use Each

| Situation | Concept to load |
|-----------|----------------|
| Porting a Godot 3.x project or script | [migration/godot-4.md](migration/godot-4.md) |
| Writing GDScript with signals and state machines | [patterns/scripts.md](patterns/scripts.md) |
| Creating HUD, menus, or responsive layouts | [patterns/ui.md](patterns/ui.md) |
| Instantiating scenes or loading assets at runtime | [patterns/resource-loading.md](patterns/resource-loading.md) |
| Configuring keyboard/gamepad input | [patterns/input-mapping.md](patterns/input-mapping.md) |
| Creating a character scene (player, enemy, NPC) | [checklists/character-scene.md](checklists/character-scene.md) |
| Organizing project folders for scalability | [checklists/project-structure.md](checklists/project-structure.md) |
| Setting up collision layers and masks | [reference/physics-collision.md](reference/physics-collision.md) |
| Exposing variables to the Inspector | [reference/exported-vars.md](reference/exported-vars.md) |
| Referencing nodes with $ or get_node() | [reference/node-paths.md](reference/node-paths.md) |
| Building a new .tscn file from scratch | [scene/structures.md](scene/structures.md) |

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

Load concepts as context before generating Godot code:

```
# Before writing code, read the relevant concept:
read knowledge/migration/godot-4.md

# Then generate Godot 4.7 code using the patterns from the concept.
```

Always verify generated code against the relevant checklist before returning
results to the user.
