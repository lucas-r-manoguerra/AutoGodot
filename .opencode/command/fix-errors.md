---
description: Parse Godot error output and fix the issues
---

Take the Godot error output (from clipboard or argument $ARGUMENTS) and:

1. Parse errors using `godot_errors` MCP tool
2. Locate the problematic files using the parsed output
3. Fix each error in the source files
4. Re-run `run_godot_test` to verify fixes
5. Report what was fixed and any remaining issues
