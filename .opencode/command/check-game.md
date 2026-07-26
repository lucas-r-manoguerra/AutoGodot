---
description: Run full project validation (syntax, structure, optimization)
---

Use `gdcheck`, `gdvalidate`, and `gdoptimize` MCP tools to perform a full project audit.

Steps:
1. Call `gdcheck` with empty file_path (all files)
2. Call `gdvalidate` for compliance check
3. Call `gdoptimize` for optimization opportunities
4. Report findings organized by severity: errors first, then warnings, then suggestions
