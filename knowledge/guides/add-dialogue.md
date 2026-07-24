---
title: "Add Dialogue System"
type: guide
category: feature
difficulty: intermediate
estimated_time: "1-2 hours"
prerequisites: ["add-collisions.md"]
version: "4.7"
created: "2026-07-24"
status: active
---

# Add Dialogue System

How to implement a dialogue system with branching conversations.

## Overview

**What you'll learn:**
- Dialogue data structure
- Dialogue UI
- Branching conversations
- Dialogue triggers

---

## Dialogue Data Structure

### Create dialogue.gd

```gdscript
extends Resource
class_name Dialogue

@export var dialogue_name: String = ""
@export var lines: Array[DialogueLine] = []
```

### Create dialogue_line.gd

```gdscript
extends Resource
class_name DialogueLine

@export var speaker: String = ""
@export var text: String = ""
@export var choices: Array[DialogueChoice] = []
@export var next_line_index: int = -1  # -1 = end dialogue
```

### Create dialogue_choice.gd

```gdscript
extends Resource
class_name DialogueChoice

@export var text: String = ""
@export var next_line_index: int = 0
@export var condition: String = ""  # Optional condition
```

---

## Dialogue Manager

### Create dialogue_manager.gd

```gdscript
extends Node

signal dialogue_started
signal dialogue_ended
signal line_displayed(speaker: String, text: String)
signal choices_presented(choices: Array[DialogueChoice])

var current_dialogue: Dialogue
var current_line_index: int = 0
var is_active: bool = false

func start_dialogue(dialogue: Dialogue) -> void:
    current_dialogue = dialogue
    current_line_index = 0
    is_active = true
    dialogue_started.emit()
    _show_current_line()

func _show_current_line() -> void:
    if current_line_index >= current_dialogue.lines.size():
        _end_dialogue()
        return

    var line = current_dialogue.lines[current_line_index]
    line_displayed.emit(line.speaker, line.text)

    if line.choices.size() > 0:
        choices_presented.emit(line.choices)
    elif line.next_line_index >= 0:
        current_line_index = line.next_line_index
        _show_current_line()
    else:
        current_line_index += 1

func select_choice(choice_index: int) -> void:
    var line = current_dialogue.lines[current_line_index]
    var choice = line.choices[choice_index]
    current_line_index = choice.next_line_index
    _show_current_line()

func advance() -> void:
    var line = current_dialogue.lines[current_line_index]
    if line.choices.size() == 0:
        if line.next_line_index >= 0:
            current_line_index = line.next_line_index
        else:
            current_line_index += 1
        _show_current_line()

func _end_dialogue() -> void:
    is_active = false
    current_dialogue = null
    dialogue_ended.emit()
```

---

## Dialogue UI

### Create dialogue_ui.gd

```gdscript
extends CanvasLayer

@onready var panel: PanelContainer = $Panel
@onready var speaker_label: Label = $Panel/MarginContainer/VBoxContainer/SpeakerLabel
@onready var text_label: Label = $Panel/MarginContainer/VBoxContainer/TextLabel
@onready var choices_container: VBoxContainer = $Panel/MarginContainer/VBoxContainer/ChoicesContainer

var dialogue_manager: Node

func _ready() -> void:
    dialogue_manager = get_node("/root/DialogueManager")
    dialogue_manager.line_displayed.connect(_on_line_displayed)
    dialogue_manager.choices_presented.connect(_on_choices_presented)
    dialogue_manager.dialogue_ended.connect(_on_dialogue_ended)
    hide()

func _on_line_displayed(speaker: String, text: String) -> void:
    show()
    speaker_label.text = speaker
    text_label.text = text
    choices_container.visible = false

func _on_choices_presented(choices: Array[DialogueChoice]) -> void:
    choices_container.visible = true
    # Clear old choices
    for child in choices_container.get_children():
        child.queue_free()

    # Create choice buttons
    for i in range(choices.size()):
        var button = Button.new()
        button.text = choices[i].text
        button.pressed.connect(func(): _on_choice_selected(i))
        choices_container.add_child(button)

func _on_choice_selected(index: int) -> void:
    dialogue_manager.select_choice(index)

func _on_dialogue_ended() -> void:
    hide()

func _unhandled_input(event: InputEvent) -> void:
    if dialogue_manager.is_active and event.is_action_pressed("ui_accept"):
        dialogue_manager.advance()
```

---

## Dialogue Trigger

### Create dialogue_trigger.gd

```gdscript
extends Area2D

@export var dialogue: Dialogue

var player_in_range: bool = false

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        player_in_range = true

func _on_body_exited(body: Node2D) -> void:
    if body.is_in_group("player"):
        player_in_range = false

func _unhandled_input(event: InputEvent) -> void:
    if player_in_range and event.is_action_pressed("interact"):
        var dialogue_manager = get_node("/root/DialogueManager")
        dialogue_manager.start_dialogue(dialogue)
```

---

## Example Dialogue

### Create example dialogue resource

```gdscript
# In editor or code
var dialogue = Dialogue.new()
dialogue.dialogue_name = "villager_greeting"

var line1 = DialogueLine.new()
line1.speaker = "Villager"
line1.text = "Hello, traveler! Welcome to our village."
line1.next_line_index = 1

var line2 = DialogueLine.new()
line2.speaker = "Villager"
line2.text = "How can I help you today?"
line2.choices = [
    {"text": "Tell me about the village", "next_line_index": 2},
    {"text": "Do you have any quests?", "next_line_index": 3},
    {"text": "Goodbye", "next_line_index": -1}
]

dialogue.lines = [line1, line2]
```

---

## Gotchas

1. **Input handling**: Disable player movement during dialogue
2. **UI layers**: Use CanvasLayer for dialogue UI
3. **Typing effect**: Add character-by-character reveal for polish
4. **Conditions**: Check game state for conditional choices
5. **Save system**: Serialize dialogue state for saves

---

## Cross-References

- [Add Collisions Guide](add-collisions.md) — Area2D for triggers
- [UI Patterns](../patterns/ui.md) — UI best practices
- [Script Patterns](../patterns/scripts.md) — Common patterns
- [Build Main Menu](build-main-menu.md) — Menu UI patterns
