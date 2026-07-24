# Design: Game Logic API

## Technical Approach

Mirror the `SceneBuilder` pattern for `.gd` files. New `ScriptBuilder` class in `core/script_builder.py` provides `create()`, `read()`, and `modify()` methods that convert between structured JSON and GDScript text. All GDScript generation uses Python string templates with tab indentation. All parsing uses compiled regex patterns — no external parser. Three new MCP tools register via Pydantic input models in `mcp_server.py`.

## Architecture Decisions

| Decision | Options | Tradeoff | Choice |
|----------|---------|----------|--------|
| Parsing strategy | Regex vs tree-sitter vs hand-recursive | Regex: no deps, sufficient for flat GDScript. Tree-sitter: accurate but heavy dep. Hand-recursive: fragile. | **Regex** — zero deps, covers v1 scope |
| Template engine | Python f-strings vs Jinja2 vs manual join | F-strings: simple, fast, no dep. Jinja2: powerful but overkill. Manual: error-prone. | **f-strings** — matches project style |
| Section ordering | Fixed order vs preserve source order | Fixed: predictable, simpler. Preserve: harder, comments complicate. | **Fixed order** — out of scope to preserve formatting |
| Indentation | Hardcode `\t` vs configurable | Hardcode: simpler, Godot standard. Configurable: unnecessary complexity. | **Hardcode `\t`** — Godot convention |

## Module Structure

```
core/
├── scene_builder.py      (existing — no changes)
├── script_builder.py     (NEW — ScriptBuilder class)
├── mcp_server.py         (MODIFY — add 3 tools + 3 input models)
└── ...

tests/
├── test_script_builder.py  (NEW)
└── ...
```

## Class Design: ScriptBuilder

```python
class ScriptBuilder:
    """Structured read/create/modify for GDScript (.gd) files."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()

    # Public API — all return str ("OK: ..." or "ERROR: ...")
    def create(self, script_path: str, definition: dict) -> str: ...
    def read(self, script_path: str) -> dict | str: ...
    def modify(self, script_path: str, operations: list[dict]) -> str: ...

    # Path security (identical to SceneBuilder)
    def _validate_path(self, script_path: str) -> Path | str: ...
```

### create(script_path, definition) → str

Accepts a structured definition dict, writes a `.gd` file.

**Definition schema:**
```python
{
    "extends": "CharacterBody2D",           # optional, default "Node"
    "class_name": "Player",                 # optional
    "signals": ["died", "health_changed"],  # optional
    "variables": [                           # optional
        {"name": "speed", "type": "float", "value": "200.0", "export": true},
        {"name": "health", "type": "int", "value": "100"},
    ],
    "functions": [                           # optional
        {
            "name": "_ready",
            "args": "",
            "body": ["\tpass"]               # list of lines, tab-indented
        },
    ],
}
```

**Output order** (fixed, non-configurable):
1. `extends` line
2. `class_name` line
3. blank line + `signal` declarations
4. blank line + `@export` variables
5. blank line + regular variables
6. blank line + functions (each with blank line separator)

### read(script_path) → dict | str

Parses a `.gd` file into the same schema as `create`'s definition, plus a `"body"` key containing raw lines for functions.

**Return dict:**
```python
{
    "extends": "CharacterBody2D",
    "class_name": "Player",
    "signals": ["died"],
    "variables": [
        {"name": "speed", "type": "float", "value": "200.0", "export": true}
    ],
    "functions": [
        {"name": "_ready", "args": "", "body": ["\tpass"]}
    ],
    "metadata": {"lines": 15, "path": "scripts/player.gd"}
}
```

### modify(script_path, operations) → str

Load → mutate → serialize. Operations applied in order.

**Operation types:**

| Action | Required Fields | Behavior |
|--------|----------------|----------|
| `add_signal` | `name` | Append signal declaration |
| `remove_signal` | `name` | Delete signal line |
| `add_variable` | `name`, optional: `type`, `value`, `export` | Append variable declaration |
| `remove_variable` | `name` | Delete variable line |
| `add_function` | `name`, `args`, `body` | Append function block |
| `remove_function` | `name` | Delete function block (name through next `func`/EOF) |
| `replace_function_body` | `name`, `body` | Replace lines inside function |
| `set_extends` | `value` | Replace extends line |
| `set_class_name` | `value` | Replace or add class_name line |

## Regex Patterns for Parsing

All patterns are compiled at module level (`re.compile`).

```python
# Header
_RE_EXTENDS    = re.compile(r"^extends\s+(\w+)", re.MULTILINE)
_RE_CLASS_NAME = re.compile(r"^class_name\s+(\w+)", re.MULTILINE)

# Declarations
_RE_SIGNAL     = re.compile(r"^signal\s+(\w+)", re.MULTILINE)
_RE_VARIABLE   = re.compile(
    r"^(?P<export>@export\s+)?var\s+(?P<name>\w+)"
    r"(?:\s*:\s*(?P<type>\w+))?"
    r"(?:\s*=\s*(?P<value>.+))?",
    re.MULTILINE,
)

# Functions
_RE_FUNC_START = re.compile(r"^func\s+(\w+)\s*\(([^)]*)\)\s*:", re.MULTILINE)
_RE_FUNC_BODY  = re.compile(
    r"^func\s+\w+\s*\([^)]*\)\s*:\s*\n(?P<body>(?:\t.*\n?)*)",
    re.MULTILINE,
)
```

**Body capture strategy:** `_RE_FUNC_BODY` captures all lines starting with `\t` after the `func` header. The body is split on `\n` to produce the line list. This correctly handles multi-line bodies, nested indents, and blank lines within the function. It fails on functions with no body (empty body → empty string, handled).

## Template Strings for Generation

```python
TPL_EXTENDS    = "extends {extends}"
TPL_CLASS_NAME = "class_name {class_name}"
TPL_SIGNAL     = "signal {name}"
TPL_VAR_EXPORT = "@export var {name}: {type} = {value}"
TPL_VAR_TYPED  = "var {name}: {type} = {value}"
TPL_VAR_UNTYPED = "var {name} = {value}"
TPL_FUNC       = "func {name}({args}):\n{body}"
```

Generated sections joined with `"\n\n"` (blank line separator). No trailing newline added by builder — `Path.write_text()` handles it.

## Error Handling

Follows SceneBuilder pattern exactly:

- All public methods return `str` on error: `"ERROR: ..."`
- Path traversal → `_validate_path()` returns error string
- File not found → explicit check before parse
- Parse failures → `try/except` wrapping, return `"ERROR reading script ..."`
- Unknown operation in `modify()` → `"ERROR: Unknown action: {action}"`
- No exceptions leak to MCP layer

## Integration with mcp_server.py

**3 new Pydantic input models:**

```python
class CreateScriptInput(BaseModel):
    script_path: str = Field(..., description="Relative path for the .gd file")
    definition: dict = Field(..., description="Script definition dict")

class ReadScriptInput(BaseModel):
    script_path: str = Field(..., description="Relative path to the .gd file")

class ModifyScriptInput(BaseModel):
    script_path: str = Field(..., description="Relative path to the .gd file")
    operations: list[dict] = Field(..., description="List of operations")
```

**3 new tool registrations:**

```python
@mcp.tool()
async def create_script(script_path: str, definition: dict) -> str: ...
@mcp.tool()
async def read_script(script_path: str) -> str: ...
@mcp.tool()
async def modify_script(script_path: str, operations: list[dict]) -> str: ...
```

Each tool delegates to `script_builder.create/read/modify()`, wraps result in `str()`, catches exceptions returning `"ERROR: ..."`.

**Module-level instantiation:**

```python
from core.script_builder import ScriptBuilder
script = ScriptBuilder(project_dir=GODOT_PROJECT)
```

## Data Flow

```
LLM Agent
  │
  ▼ (MCP call)
mcp_server.py  ──→  ScriptBuilder.create/read/modify()
  │                      │
  │                      ├── validate path
  │                      ├── read/write .gd file
  │                      ├── regex parse / template generate
  │                      └── return dict or "OK/ERROR" string
  │
  ▼ (response)
LLM Agent
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Each regex pattern in isolation | Direct `pattern.search()` assertions |
| Unit | `_validate_path` traversal rejection | Same as SceneBuilder tests |
| Unit | `create()` output structure | Write → read back → compare keys |
| Unit | `read()` parsing accuracy | Hand-crafted `.gd` fixtures → assert dict values |
| Unit | `modify()` each operation type | Read → modify → read → assert change |
| Integration | Round-trip: create → read → compare | Create from def, read back, assert equivalence |
| Integration | MCP tool wrappers | Mock `ScriptBuilder`, verify delegation + error handling |
| Edge cases | Empty body, no extends, nested indents | Dedicated test cases per edge |

Coverage target: 80%+ for `core/script_builder.py`.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Additive change — `write_game_file` remains for raw text. No existing behavior changes.

## Open Questions

- [ ] None — scope is clear from proposal. All decisions have rationale above.
