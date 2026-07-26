---
description: Run the Godot project and report any errors
---

Use the `run_godot_test` MCP tool to launch the Godot project. Parse any errors from the output and report them with file locations and suggested fixes.

Steps:
1. Call `run_godot_test` with default args (30s timeout)
2. If output contains errors, call `godot_errors` to parse them
3. Report structured findings: file, line, error type, suggested fix
4. If no errors, confirm clean run with duration
