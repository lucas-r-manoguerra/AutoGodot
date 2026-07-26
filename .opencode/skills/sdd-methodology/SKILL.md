---
name: sdd-methodology
description: "Spec-Driven Development workflow for game projects. Triggers on: SDD, spec-driven, proposal, design document, methodology, workflow phases."
---

# SDD (Spec-Driven Development) for Game Development

Structured workflow for building game features with clear phases and gates.

## Phases

### 1. Explore
- Understand the user's request
- Check existing codebase state (files, patterns, conventions)
- Identify constraints and dependencies
- Output: **Exploration Report**

### 2. Propose
- Define intent, scope, and approach
- List affected files and systems
- Identify risks and open questions
- Output: **Proposal Document**

### 3. Spec
- Write detailed specifications with scenarios
- Define acceptance criteria for each feature
- Specify data contracts (Resources, signals)
- Output: **Delta Spec**

### 4. Design
- Choose architecture patterns (ECS, State Machine, etc.)
- Define scene tree structure
- Design signal contracts between nodes
- Output: **Design Document**

### 5. Tasks
- Break design into implementation tasks
- One file = one task (200 line max)
- Order by dependency (independent tasks first)
- Output: **Task List**

### 6. Apply
- Implement tasks via sub-agents
- Follow project conventions (type hints, signals, @export)
- Write .tscn and .gd files directly
- Output: **Implemented Code**

### 7. Verify
- Run gdcheck on all scripts
- Run gdvalidate on project
- Run headless game test
- Capture screenshot for visual QA
- Output: **Verification Report**

### 8. Archive
- Save decisions and discoveries to engram
- Update knowledge base if new patterns emerged
- Output: **Archive Summary**

## Quality Gates

Between phases, validate:
- [ ] Phase objective achieved
- [ ] No drift from original requirements
- [ ] Conventions followed (type hints, one file = one task)
- [ ] All files pass gdcheck

## When to Use SDD

- New feature with 3+ files to create
- Architecture decision with tradeoffs
- Complex system (state machine, inventory, dialogue)
- Anything the user explicitly asks to "plan first"

## When to Skip SDD

- Single-file bug fix
- Simple property change
- User says "just do it" or equivalent
