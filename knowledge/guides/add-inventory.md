---
title: "Add Inventory System"
type: guide
category: feature
difficulty: intermediate
estimated_time: "1-2 hours"
prerequisites: ["add-collisions.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Add Inventory System

How to implement an inventory system with UI in Godot 4.7.

## Overview

**What you'll learn:**
- Inventory data structure
- Item pickup with signals
- Inventory UI display
- Item stacking and usage

---

## Inventory Data Structure

### Create inventory.gd

```gdscript
extends Node
class_name Inventory

signal inventory_changed
signal item_added(item: InventoryItem)
signal item_removed(item: InventoryItem)

@export var max_slots: int = 20

var items: Array[InventoryItem] = []

func add_item(item: InventoryItem) -> bool:
    if items.size() >= max_slots:
        return false

    # Check for stackable item
    for existing in items:
        if existing.id == item.id and existing.stackable:
            existing.quantity += item.quantity
            inventory_changed.emit()
            item_added.emit(item)
            return true

    # Add new item
    items.append(item)
    inventory_changed.emit()
    item_added.emit(item)
    return true

func remove_item(item: InventoryItem) -> bool:
    var index = items.find(item)
    if index == -1:
        return false

    items.remove_at(index)
    inventory_changed.emit()
    item_removed.emit(item)
    return true

func has_item(item_id: String) -> bool:
    for item in items:
        if item.id == item_id:
            return true
    return false

func get_item_count(item_id: String) -> int:
    for item in items:
        if item.id == item_id:
            return item.quantity
    return 0
```

### Create inventory_item.gd

```gdscript
extends Resource
class_name InventoryItem

@export var id: String = ""
@export var name: String = ""
@export var description: String = ""
@export var icon: Texture2D
@export var stackable: bool = true
@export var max_stack: int = 99
@export var quantity: int = 1
```

---

## Item Pickup

### Create pickup.gd

```gdscript
extends Area2D

@export var item: InventoryItem

signal picked_up(item: InventoryItem)

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        var inventory = body.get_node_or_null("Inventory")
        if inventory and inventory.add_item(item.duplicate()):
            picked_up.emit(item)
            queue_free()
```

### Create pickup scene

```
[gd_scene load_steps=3]

[ext_resource type="Script" path="res://scripts/pickup.gd" id="1"]
[ext_resource type="Resource" path="res://resources/items/sword.tres" id="2"]

[sub_resource type="CircleShape2D" id="1"]
radius = 16.0

[node name="Pickup" type="Area2D"]
script = ExtResource("1")
item = ExtResource("2")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
```

---

## Inventory UI

### Create inventory_ui.gd

```gdscript
extends Control

@onready var grid: GridContainer = $ScrollContainer/GridContainer
@onready var item_name_label: Label = $ItemNameLabel
@onready var item_desc_label: Label = $ItemDescLabel

var inventory: Inventory
var slot_scene = preload("res://scenes/ui/inventory_slot.tscn")

func _ready() -> void:
    # Find player's inventory
    var player = get_tree().get_first_node_in_group("player")
    if player:
        inventory = player.get_node("Inventory")
        inventory.inventory_changed.connect(_on_inventory_changed)
        _refresh_ui()

func _on_inventory_changed() -> void:
    _refresh_ui()

func _refresh_ui() -> void:
    # Clear existing slots
    for child in grid.get_children():
        child.queue_free()

    # Create slots
    for item in inventory.items:
        var slot = slot_scene.instantiate()
        slot.setup(item)
        slot.item_selected.connect(_on_item_selected)
        grid.add_child(slot)

func _on_item_selected(item: InventoryItem) -> void:
    item_name_label.text = item.name
    item_desc_label.text = item.description
```

### Create inventory_slot.gd

```gdscript
extends PanelContainer

signal item_selected(item: InventoryItem)

var current_item: InventoryItem

@onready var icon: TextureRect = $Icon
@onready var quantity_label: Label = $QuantityLabel

func setup(item: InventoryItem) -> void:
    current_item = item
    icon.texture = item.icon
    if item.quantity > 1:
        quantity_label.text = str(item.quantity)
        quantity_label.visible = true
    else:
        quantity_label.visible = false

func _on_gui_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        item_selected.emit(current_item)
```

---

## Using Items

### Create item_database.gd

```gdscript
extends Node

var items: Dictionary = {}

func _ready() -> void:
    # Load all items from resources/items/
    var dir = DirAccess.open("res://resources/items")
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if file_name.ends_with(".tres"):
                var item = load("res://resources/items/" + file_name)
                if item is InventoryItem:
                    items[item.id] = item
            file_name = dir.get_next()

func get_item(id: String) -> InventoryItem:
    return items.get(id)
```

### Use consumable item

```gdscript
# In player.gd
func use_item(item: InventoryItem) -> void:
    match item.id:
        "health_potion":
            health = min(health + 20, max_health)
            inventory.remove_item(item)
        "speed_boost":
            apply_speed_boost(5.0)
            inventory.remove_item(item)
```

---

## Gotchas

1. **Duplicate resources**: Use `.duplicate()` when adding to inventory
2. **Signal connections**: Connect inventory_changed in _ready()
3. **UI refresh**: Only rebuild UI when inventory changes
4. **Item references**: Store by ID, not reference
5. **Save/load**: Serialize inventory to dictionary for saving

---

## Cross-References

- [Add Collisions Guide](add-collisions.md) — Area2D for pickups
- [UI Patterns](../patterns/ui.md) — UI best practices
- [Exported Variables](../reference/exported-vars.md) — @export for items
