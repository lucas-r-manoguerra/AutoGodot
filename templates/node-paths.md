# Node Paths

How to reference nodes in Godot: `$` shorthand, `get_node()`, groups, and path conventions.

## The `$` Shorthand

`$NodeName` is equivalent to `get_node("NodeName")`. Both resolve paths relative to the current node.

```gdscript
# These are identical:
var sprite = $Sprite2D
var sprite = get_node("Sprite2D")

# Nested paths:
var gun = $RightHand/Gun
var gun = get_node("RightHand/Gun")
```

---

## Path Types

| Path | Meaning | Example |
|------|---------|---------|
| `"."` | Current node | `get_node(".")` |
| `".."` | Parent node | `get_node("..")` |
| `"ChildName"` | Direct child | `$Sprite2D` |
| `"Parent/Child"` | Nested path | `$HUD/ScoreLabel` |
| `"../Sibling"` | Sibling node | `get_node("../Enemy")` |
| `"/root/Main/Player"` | Absolute path | Avoid — fragile |

---

## When to Use What

### `$` (Shorthand)

Use for direct child references — clean and fast:

```gdscript
extends CharacterBody2D

@onready var sprite = $Sprite2D
@onready var collision = $CollisionShape2D
@onready var animation = $AnimationPlayer
```

### `get_node()` (Dynamic)

Use when the path is constructed at runtime:

```gdscript
func get_ui_label(label_name: String) -> Label:
    return get_node("HUD/" + label_name)

# Usage
var score = get_ui_label("ScoreLabel")
```

### `get_node_or_null()` (Safe)

Use when the node might not exist:

```gdscript
var camera = get_node_or_null("Camera2D")
if camera:
    camera.make_current()
```

---

## @onready for Child Nodes

Cache node references at startup — don't search the tree every frame:

```gdscript
# ✗ BAD — searches tree every frame
func _process(delta):
    $HUD/ScoreLabel.text = str(score)

# ✓ GOOD — cached reference
@onready var score_label = $HUD/ScoreLabel

func _process(delta):
    score_label.text = str(score)
```

---

## Groups

Groups let you find nodes without knowing their path. Add nodes to groups in the editor or in code:

```gdscript
# Add to group in code
func _ready():
    add_group("enemies")

# Find all nodes in a group
var enemies = get_tree().get_nodes_in_group("enemies")
for enemy in enemies:
    enemy.take_damage(10)

# Check if node is in a group
if is_in_group("enemies"):
    print("I'm an enemy!")

# Remove from group
remove_from_group("enemies")
```

### When to Use Groups

| Use Case | Approach |
|----------|----------|
| Find all enemies | `get_tree().get_nodes_in_group("enemies")` |
| Find player from enemy | `get_tree().get_first_node_in_group("player")` |
| Notify all enemies | Loop `get_nodes_in_group` + call method |
| Check node type | `is_in_group("player")` |

---

## Avoid Absolute Paths

```gdscript
# ✗ BAD — breaks if scene tree changes
var player = get_node("/root/Main/Game/Player")

# ✓ GOOD — relative path
var player = $Player

# ✓ GOOD — group-based
var player = get_tree().get_first_node_in_group("player")
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Absolute paths (`/root/...`) | Breaks when scene restructured | Use relative paths or groups |
| `get_node()` every frame | Performance waste | Cache with `@onready` |
| Wrong path in `$` | Null reference crash | Verify node exists in scene tree |
| Using `$` for dynamic paths | Can't construct paths at runtime | Use `get_node()` with string building |
| Forgetting `@onready` | Null reference — variable set before child exists | Move initialization to `@onready` |
