# Exploration: Game Logic API

## Current State

AutoGodot is a Python MCP server (FastMCP) that exposes Godot 4.7 tools to AI agents. The current toolset focuses on **scene manipulation** and **file I/O**:

| Tool | Purpose | Structured? |
|------|---------|:-----------:|
| `write_game_file` | Create/edit any text file (.gd, .tscn, etc.) | ❌ Raw text |
| `run_godot_test` | Launch Godot, capture output | N/A |
| `capture_game_screen` | Screenshot running game | N/A |
| `read_scene` | Parse .tscn → JSON | ✅ via godot-parser |
| `create_scene` | Build .tscn from JSON | ✅ via godot-parser |
| `modify_scene` | Surgical .tscn edits | ✅ via godot-parser |

**Key insight:** Scene files have structured manipulation via `godot-parser`. GDScript files (.gd) have **no structured parser** — they're written as raw text via `write_game_file`.

## Affected Areas

- `core/mcp_server.py` — Add new MCP tool registrations + Pydantic input models
- `core/scene_builder.py` — Potential home for script builder logic (or new `script_builder.py`)
- `tests/test_mcp_server.py` — Add tool existence tests
- `tests/` — New test file for script builder

## GDScript Structure Analysis

GDScript has a well-defined grammar. Here's the anatomy:

```gdscript
extends CharacterBody2D          # Inheritance
class_name Player                # Optional class registration

# Signals
signal died                      # Simple signal
signal health_changed(old: int, new: int)  # Signal with parameters

# Exported variables
@export var speed: float = 200.0
@export var max_health: int = 100
@export_group("Combat")
@export var attack_damage: int = 10

# Internal variables
var health: int = 100
var _is_invincible: bool = false

# Constants
const MAX_SPEED = 400.0

# Ready function
func _ready() -> void:
    health = max_health

# Physics process
func _physics_process(delta: float) -> void:
    var velocity = Vector2.ZERO
    if Input.is_action_pressed("move_right"):
        velocity.x += speed
    move_and_slide()

# Custom function
func take_damage(amount: int) -> void:
    health -= amount
    health_changed.emit(health + amount, health)
    if health <= 0:
        died.emit()

# Static function
static func create_default() -> Player:
    var p = Player.new()
    p.speed = 200.0
    return p
```

### GDScript Grammar Elements

| Element | Syntax | Structured Representation |
|---------|--------|---------------------------|
| Extends | `extends Node2D` | `extends` field |
| Class name | `class_name Player` | `class_name` field |
| Signals | `signal died` / `signal health_changed(old: int, new: int)` | `signals` list |
| Exports | `@export var speed: float = 200.0` | `exports` list with type hints |
| Variables | `var health: int = 100` | `variables` list |
| Constants | `const MAX = 42` | `constants` list |
| Functions | `func _ready() -> void:` | `functions` list with body |
| Inner classes | `class MyInner:` | `inner_classes` list |
| Annotations | `@onready`, `@tool` | `annotations` list |

### Edge Cases

1. **Inheritance chains:** `extends BasePlayer` where `BasePlayer` is a custom class
2. **Signals with parameters:** `signal health_changed(old: int, new: int)`
3. **Export hints:** `@export_range(0, 100)`, `@export_file("*.png")`, `@export_group`
4. **Type hints:** Both for variables (`var x: int`) and return types (`-> void`)
5. **Default values:** `var speed: float = 200.0` — can be complex (Vector2, Color, etc.)
6. **Function bodies:** Multi-line with indentation, not just signatures
7. **Static functions:** `static func create() -> Node:`
8. **Virtual methods:** `_ready()`, `_process()`, `_physics_process()` — naming conventions
9. **Await/async:** `await get_tree().create_timer(1.0).timeout`
10. **Enums:** `enum State { IDLE, RUNNING, JUMPING }`
11. **Lambda:** `func():` inline (GDScript 4.x)
12. **Comments:** `##` docstrings, `#` inline comments

## Approaches

### Approach 1: Template-Based Generation (Recommended)

Generate GDScript from structured JSON using string templates/jinja2. No parsing needed.

```python
class ScriptBuilder:
    def create(self, script_path: str, definition: dict) -> str:
        """Create a .gd file from structured JSON definition."""
        # Build GDScript text from components
        lines = []
        
        # extends
        if definition.get("extends"):
            lines.append(f"extends {definition['extends']}")
        
        # class_name
        if definition.get("class_name"):
            lines.append(f"class_name {definition['class_name']}")
        
        # signals
        for sig in definition.get("signals", []):
            params = ", ".join(f"{p['name']}: {p['type']}" for p in sig.get("parameters", []))
            if params:
                lines.append(f"signal {sig['name']}({params})")
            else:
                lines.append(f"signal {sig['name']}")
        
        # variables
        for var in definition.get("variables", []):
            prefix = "@export " if var.get("exported") else ""
            type_hint = f": {var['type']}" if var.get("type") else ""
            default = f" = {var['default']}" if var.get("default") is not None else ""
            lines.append(f"{prefix}var {var['name']}{type_hint}{default}")
        
        # functions
        for func in definition.get("functions", []):
            params = ", ".join(f"{p['name']}: {p.get('type', 'Variant')}" for p in func.get("parameters", []))
            return_type = f" -> {func['return_type']}" if func.get("return_type") else ""
            lines.append(f"func {func['name']}({params}){return_type}:")
            # Indent body lines
            for body_line in func.get("body", []):
                lines.append(f"\t{body_line}")
            lines.append("")
        
        return "\n".join(lines)
```

**Pros:**
- Simple, predictable output
- No external dependencies beyond what exists
- Follows the `SceneBuilder` pattern (JSON → file)
- Easy to test (input JSON → output text)
- LLMs can easily construct JSON

**Cons:**
- No parsing of existing GDScript (write-only)
- Can't modify existing scripts structurally
- Must handle all edge cases manually

**Effort:** Low

### Approach 2: AST-Based with Tree-sitter

Use tree-sitter GDScript grammar for full parsing and modification.

**Pros:**
- Full round-trip: parse → modify → serialize
- Can read existing scripts
- Handles all edge cases automatically

**Cons:**
- Heavy dependency (tree-sitter + grammar)
- Complex implementation
- Overkill for initial version
- tree-sitter GDScript grammar maturity is uncertain

**Effort:** High

### Approach 3: Hybrid — Template Write + Regex Read

Template-based for creation, regex parsing for reading/modification.

**Pros:**
- Can read existing scripts (basic)
- Simpler than full AST
- Incremental capability

**Cons:**
- Regex is fragile for GDScript syntax
- Maintenance burden
- Inconsistent behavior

**Effort:** Medium

## Recommended API Design

### Tool 1: `create_script`

```python
class CreateScriptInput(BaseModel):
    script_path: str = Field(..., description="Relative path, e.g. 'scripts/player.gd'")
    definition: dict = Field(..., description="Script structure definition")
```

Definition schema:
```json
{
  "extends": "CharacterBody2D",
  "class_name": "Player",
  "signals": [
    {"name": "died"},
    {"name": "health_changed", "parameters": [
      {"name": "old_value", "type": "int"},
      {"name": "new_value", "type": "int"}
    ]}
  ],
  "variables": [
    {"name": "speed", "type": "float", "default": "200.0", "exported": true},
    {"name": "health", "type": "int", "default": "100"},
    {"name": "_is_invincible", "type": "bool", "default": "false"}
  ],
  "constants": [
    {"name": "MAX_SPEED", "value": "400.0"}
  ],
  "functions": [
    {
      "name": "_ready",
      "parameters": [],
      "return_type": "void",
      "body": ["health = max_health"]
    },
    {
      "name": "take_damage",
      "parameters": [{"name": "amount", "type": "int"}],
      "return_type": "void",
      "body": [
        "health -= amount",
        "health_changed.emit(health + amount, health)",
        "if health <= 0:",
        "\tdied.emit()"
      ]
    }
  ]
}
```

### Tool 2: `add_signal`

```python
class AddSignalInput(BaseModel):
    script_path: str
    signal_name: str
    parameters: list[dict] = Field(default_factory=list)
    # parameters: [{"name": "value", "type": "int"}]
```

### Tool 3: `add_variable`

```python
class AddVariableInput(BaseModel):
    script_path: str
    name: str
    type_hint: str | None = None
    default_value: str | None = None
    exported: bool = False
    export_hint: str | None = None  # e.g. "@export_range(0, 100)"
```

### Tool 4: `add_function`

```python
class AddFunctionInput(BaseModel):
    script_path: str
    name: str
    parameters: list[dict] = Field(default_factory=list)
    return_type: str | None = None
    body: list[str] = Field(default_factory=list)
    is_static: bool = False
```

### Tool 5: `connect_signal`

This already exists in `modify_scene` for scene-level connections. For script-level:

```python
class ConnectSignalInput(BaseModel):
    script_path: str
    signal_name: str
    target_node: str  # Path to node in scene tree
    method_name: str
```

**Note:** Script-level signal connections are typically done in `_ready()` or in the scene editor. The `modify_scene` tool already handles scene connections. This tool would add the `signal.connect(handler)` call to the script body.

## Implementation Recommendation

**Phase 1: `create_script` only**

Start with the `create_script` tool using Approach 1 (template-based). This covers 80% of use cases:
- AI agents create new scripts from scratch
- Structured JSON is easier for LLMs than raw GDScript text
- Follows the existing `SceneBuilder` pattern

**Phase 2: `read_script` (optional)**

Add basic GDScript parsing for inspection. Can use regex or simple state machine:
- Extract extends, class_name, signals, variables, functions
- Return structured JSON similar to `read_scene`

**Phase 3: `modify_script` (optional)**

Add surgical modifications similar to `modify_scene`:
- add_signal, add_variable, add_function operations
- Requires parsing existing script first

## Risks

1. **Function body complexity:** Multi-line bodies with nested control flow are hard to represent in JSON. The `body: list[str]` approach works but loses structure.

2. **No round-trip guarantee:** Created scripts can't be reliably parsed back to the same JSON (formatting differences, comments lost).

3. **Existing script modification:** Without parsing, `add_variable` / `add_signal` would need to append to raw text, which is fragile.

4. **Export hints complexity:** `@export_range()`, `@export_file()`, `@export_group()` have different syntaxes. Must handle each case.

5. **Type hint validation:** No validation that the type hint is a valid GDScript type.

6. **Indentation sensitivity:** GDScript uses tabs for indentation. Must be consistent.

## Ready for Proposal

**Yes** — The exploration is complete. The orchestrator should:

1. Propose Phase 1 (`create_script` tool) as the initial scope
2. Use template-based generation (Approach 1)
3. Follow the `SceneBuilder` pattern for implementation
4. Include comprehensive tests for all GDScript elements

The feature is well-defined, follows existing patterns, and has clear boundaries.
