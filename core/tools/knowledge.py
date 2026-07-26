"""godot_gotchas — Common Godot pitfalls knowledge base."""

from __future__ import annotations

import json

from core.config import mcp

GODOT_GOTCHAS: list[dict[str, str]] = [
    {
        "category": "rendering",
        "title": "Control child covers parent _draw()",
        "problem": "A ColorRect/Label/Control as child of Node2D renders ON TOP of the parent's _draw(), making drawn content invisible.",
        "solution": "Use CanvasLayer for UI elements. Draw backgrounds in _draw() instead of ColorRect children. Or set the Control's z_index to -1.",
        "example": "BAD: Node2D -> ColorRect.  GOOD: Node2D + CanvasLayer -> ColorRect",
    },
    {
        "category": "rendering",
        "title": "2D and 3D nodes in same branch",
        "problem": "Mixing Node2D and Node3D in the same parent-child branch causes rendering issues or invisible nodes.",
        "solution": "Keep 2D and 3D in separate scene trees. Use separate root nodes for each dimension.",
        "example": "BAD: Node3D -> Sprite2D.  GOOD: Separate Node2D and Node3D roots.",
    },
    {
        "category": "indentation",
        "title": "Mixed tabs and spaces",
        "problem": "Godot 4.x GDScript rejects files with mixed indentation (tabs + spaces). Even one tab in a spaces file causes parse errors.",
        "solution": "Use 4 spaces consistently. Never mix. Run auto_fix after writing .gd files.",
        "example": "Line 1: '    var x' (spaces) + Line 2: '\\ty = 1' (tab) = PARSE ERROR",
    },
    {
        "category": "indentation",
        "title": "AI generates tabs when spaces expected",
        "problem": "LLMs sometimes output tab characters in GDScript code. The write_game_file tool may pass them through.",
        "solution": "Always run auto_fix after writing, or validate with gdcheck which detects mixed indentation.",
        "example": "The auto_fix tool converts all tabs to 4 spaces automatically.",
    },
    {
        "category": "architecture",
        "title": "Monolithic scripts (300+ lines)",
        "problem": "Large scripts are impossible to debug. When _draw() doesn't render, finding the root cause in 300 lines is painful.",
        "solution": "One file = one task. Split into data, logic, rendering, UI. Use preload() to connect them.",
        "example": "tetris_data.gd (constants) + tetris_board.gd (state) + tetris_draw.gd (rendering) + game.gd (orchestrator)",
    },
    {
        "category": "cli",
        "title": "class_name not indexed in CLI",
        "problem": "Godot CLI doesn't index new scripts with class_name. References fail with 'Could not find type' errors.",
        "solution": "Use preload('res://scripts/my_script.gd') instead of class_name for script references.",
        "example": "BAD: class_name MyData (referenced as MyData).  GOOD: var D = preload('res://scripts/my_data.gd')",
    },
    {
        "category": "api",
        "title": "move_and_slide() signature changed in Godot 4",
        "problem": "In Godot 3, move_and_slide(velocity). In Godot 4, move_and_slide() takes NO arguments — velocity is a property.",
        "solution": "Set velocity property before calling move_and_slide(): velocity = direction * speed; move_and_slide()",
        "example": "BAD: move_and_slide(dir * speed).  GOOD: velocity = dir * speed; move_and_slide()",
    },
    {
        "category": "api",
        "title": "String-based connect() deprecated in Godot 4",
        "problem": "signal.connect('method_name', target) is Godot 3 syntax. Fails silently in Godot 4.",
        "solution": "Use signal.connect(callable): signal.connect(target.method_name)",
        "example": "BAD: connect('hit', self, '_on_hit').  GOOD: hit.connect(_on_hit)",
    },
    {
        "category": "api",
        "title": "export/onready are annotations in Godot 4",
        "problem": "export var and onready var are Godot 3 syntax. Godot 4 uses @export and @onready.",
        "solution": "Use @export var speed: float = 100.0 and @onready var sprite = $Sprite2D",
        "example": "BAD: export var speed.  GOOD: @export var speed: float = 100.0",
    },
    {
        "category": "physics",
        "title": "CollisionShape needs CollisionObject parent",
        "problem": "CollisionShape2D/3D nodes only work under CharacterBody, Area, StaticBody, or RigidBody nodes.",
        "solution": "Always parent CollisionShape under a physics body node.",
        "example": "BAD: Node2D -> CollisionShape2D.  GOOD: CharacterBody2D -> CollisionShape2D",
    },
    {
        "category": "rendering",
        "title": "CanvasLayer for HUD/overlay",
        "problem": "UI elements drawn at the same z-level as game objects. Camera movement scrolls UI.",
        "solution": "Put all HUD elements under a CanvasLayer node. It renders on a separate canvas layer.",
        "example": "Root -> CanvasLayer -> Label (Score), Label (Health)",
    },
    {
        "category": "scene",
        "title": "unique_name_in_owner for %NodeName",
        "problem": "Using %NodeName in @onready requires the node to have unique_name_in_owner=true in the .tscn.",
        "solution": "Set 'unique_name_in_owner = true' on the node in the scene file, or use $path instead.",
        "example": "In .tscn: [node name='ScoreLabel' ...] unique_name_in_owner = true",
    },
    {
        "category": "performance",
        "title": "queue_redraw() in _process() causes constant redraws",
        "problem": "Calling queue_redraw() every frame means _draw() runs 60 times/sec. Fine for games, wasteful for static UI.",
        "solution": "Only call queue_redraw() when state changes. For static content, _draw() is called once automatically.",
        "example": "GOOD: queue_redraw() only when piece moves or board changes.",
    },
    {
        "category": "debugging",
        "title": "Godot CLI errors vs script errors",
        "problem": "Godot outputs many engine-level errors (BUG: Unreferenced static string, RID leaks) that are NOT script errors.",
        "solution": "Filter for 'SCRIPT ERROR' or 'game.gd' specifically. Engine cleanup messages at exit are normal.",
        "example": "IGNORE: 'Pages in use exist at exit in PagedAllocator'. CHECK: 'SCRIPT ERROR: Parse Error'",
    },
]


@mcp.tool()
async def godot_gotchas(category: str = "", keyword: str = "") -> str:
    """Query common Godot 4.x pitfalls and how to avoid them.

    Based on real debugging sessions. Returns relevant gotchas filtered
    by category (rendering, indentation, api, cli, physics, scene,
    architecture, performance, debugging) or keyword search.

    Args:
        category: Filter by category (optional). Leave empty for all.
        keyword: Search in title, problem, solution (optional).

    Returns JSON with matching gotchas.
    """
    results = GODOT_GOTCHAS

    if category:
        results = [g for g in results if g["category"] == category.lower()]

    if keyword:
        kw = keyword.lower()
        results = [
            g for g in results
            if kw in g["title"].lower()
            or kw in g["problem"].lower()
            or kw in g["solution"].lower()
            or kw in g["category"].lower()
        ]

    return json.dumps({
        "total": len(results),
        "gotchas": results,
    }, indent=2)
