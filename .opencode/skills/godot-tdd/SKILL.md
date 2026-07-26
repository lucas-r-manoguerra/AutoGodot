---
name: godot-tdd
description: "Test-driven development for Godot games. Triggers on: TDD, test, GdUnit4, Gut, unit test, integration test, red-green-refactor."
---

# Test-Driven Development for Godot

Red-Green-Refactor cycle adapted for game development.

## TDD Cycle

1. **Red**: Write a failing test that defines expected behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Clean up code while keeping tests green

## What to Test vs What Not to

### TEST (logic is testable)
- State machine transitions
- Health/damage calculations
- Score systems
- Inventory management
- Resource loading and data
- Event emission patterns

### DON'T TEST (rendering/visual)
- Sprite appearance
- Animation playback
- Particle effects
- Camera follow smoothness
- UI layout (use visual QA instead)

## GdUnit4 Test Structure

```gdscript
extends GutTest

var player: CharacterBody2D

func before_each() -> void:
    player = preload("res://scenes/player.tscn").instantiate()
    add_child(player)

func after_each() -> void:
    player.queue_free()

func test_player_starts_with_full_health() -> void:
    assert_eq(player.health, 100, "Player should start with 100 HP")

func test_player_takes_damage() -> void:
    player.take_damage(25)
    assert_eq(player.health, 75, "Player should have 75 HP after 25 damage")

func test_player_dies_at_zero() -> void:
    player.take_damage(100)
    assert_eq(player.health, 0, "Player should have 0 HP")
    assert_true(player.is_dead, "Player should be dead")
```

## Testing State Machines

```gdscript
func test_transitions_to_running() -> void:
    player.transition_to(player.State.RUNNING)
    assert_eq(player.current_state, player.State.RUNNING)

func test_cannot_attack_while_dead() -> void:
    player.take_damage(100)
    player.try_attack()
    assert_eq(player.current_state, player.State.IDLE, "Dead player cannot attack")
```

## Testing Signals

```gdscript
func test_emits_health_changed() -> void:
    watch_signals(player)
    player.take_damage(10)
    assert_signal_emitted(player, "health_changed")
    assert_signal_emitted_with_parameters(player, "health_changed", [90])
```

## Testing Resources

```gdscript
func test_enemy_data_defaults() -> void:
    var data = EnemyData.new()
    assert_eq(data.max_health, 50)
    assert_eq(data.speed, 150.0)
    assert_eq(data.damage, 10)

func test_loot_table_drop_rate() -> void:
    var table = LootTable.new()
    var entry = LootEntry.new()
    entry.drop_chance = 1.0
    table.entries.append(entry)
    assert_not_null(table.roll(), "100% drop rate should always drop")
```

## Mocking Godot Nodes

```gdscript
# Create mock node for testing
func _create_mock_player() -> CharacterBody2D:
    var mock = CharacterBody2D.new()
    mock.set("health", 100)
    mock.set("speed", 200.0)
    return mock

func test_system_processes_entity() -> void:
    var mock = _create_mock_player()
    add_child(mock)
    movement_system._physics_process(0.016)
    assert_gt(mock.position.x, 0.0, "Entity should move right")
    mock.queue_free()
```

## Integration Tests (Headless)

```gdscript
# test_game_flow.gd
extends GutTest

func test_scene_loads_without_errors() -> void:
    var scene = preload("res://scenes/main.tscn").instantiate()
    add_child(scene)
    assert_not_null(scene, "Main scene should load")
    await get_tree().create_timer(1.0).timeout
    scene.queue_free()

func test_player_spawns_at_start() -> void:
    var scene = preload("res://scenes/main.tscn").instantiate()
    add_child(scene)
    var player = scene.get_node("Player")
    assert_not_null(player, "Player should exist in scene")
    assert_eq(player.global_position, Vector2(100, 500))
    scene.queue_free()
```

## Running Tests

```bash
# Via autogodot MCP
run_tests(test_type="gdunit4")

# Via Godot headless
godot --headless -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Testing rendering output | Test logic only, use visual QA |
| Not cleaning up test scenes | Always queue_free() in after_each |
| Shared test state | Reset state in before_each |
| Flaky async tests | Use await with timeouts |
| Testing Godot internals | Test YOUR code, not engine behavior |
