# Development Guide

This document covers coding standards, extension patterns, and how to contribute to AutoGodot.

## Project Structure

```
autogodot/
├── core/
│   ├── __init__.py              # Package marker
│   ├── mcp_server.py            # MCP protocol handler + tool definitions
│   ├── godot_controller.py      # Godot subprocess management
│   └── vision_qa.py             # Screen capture + image processing
├── scripts/
│   └── setup_and_run.sh         # One-click Ubuntu setup
├── config/
│   └── claude_desktop_config.example.json
├── docs/                        # Documentation
│   ├── README.md                # Documentation index
│   ├── 01-architecture.md       # System architecture
│   ├── 02-reference-analysis.md # Analysis of reference projects
│   ├── 03-mcp-tools.md          # Tool API reference
│   ├── 04-setup-guide.md        # Installation guide
│   ├── 05-godot-communication.md# How we talk to Godot
│   ├── 06-visual-qa.md          # Screen capture system
│   └── 07-development-guide.md  # This file
├── .gitignore
├── requirements.txt
└── README.md
```

## Coding Standards

### Python Style

- **Python version:** 3.10+ (use `X | Y` union syntax, not `Optional[X]`)
- **Type hints:** Required on all function signatures
- **Docstrings:** Required on all public functions and classes (Google style)
- **Line length:** 100 characters max
- **Imports:** Grouped (stdlib → third-party → local), sorted alphabetically

### Example

```python
"""Module-level docstring explaining the purpose."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class MyInput(BaseModel):
    """Input schema for my tool."""

    file_path: str = Field(
        ...,
        description="Relative path to the file.",
    )
    timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Timeout in seconds.",
    )


async def my_tool(file_path: str, timeout: float = 30.0) -> str:
    """Do something useful.

    Args:
        file_path: Relative path to the file.
        timeout: Timeout in seconds.

    Returns:
        Confirmation message with details.

    Raises:
        RuntimeError: If the operation fails.
    """
    # Implementation here
    return f"OK: Processed {file_path}"
```

### MCP Tool Conventions

1. **Input is always a Pydantic BaseModel** — Even for simple tools, use a model for validation and schema generation.

2. **Output is always a string** — MCP tools return text. Use structured text (JSON-like) for complex responses.

3. **Errors return `ERROR:` prefix** — Don't raise exceptions from tools. Catch errors and return `ERROR: description` messages.

4. **Async functions** — All tool functions are async to support concurrent operations.

5. **Logging goes to stderr** — Never print to stdout (MCP uses it for protocol).

### Shell Script Style

- **Shell:** `bash` with `set -euo pipefail`
- **Comments:** Every non-trivial block
- **Functions:** Use `log_info`, `log_ok`, `log_warn`, `log_error` helpers
- **Quoting:** Always quote variables in strings

## Adding a New MCP Tool

### Step 1: Define the Input Model

In `core/mcp_server.py`, add a Pydantic model:

```python
class MyNewToolInput(BaseModel):
    """Input for my new tool."""

    param1: str = Field(
        ...,
        description="Description of param1.",
    )
    param2: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Description of param2 with constraints.",
    )
```

### Step 2: Implement the Tool Function

```python
@mcp.tool()
async def my_new_tool(param1: str, param2: int = 10) -> str:
    """One-line description of what this tool does.

    Longer description explaining when and how to use this tool.
    Include examples if the usage is non-obvious.

    Returns a confirmation with details about what was done.
    """
    logger.info("my_new_tool → param1=%s param2=%d", param1, param2)

    try:
        # Implementation
        result = do_something(param1, param2)

        msg = f"OK: {result}"
        logger.info(msg)
        return msg

    except Exception as exc:
        msg = f"ERROR my_new_tool: {exc}"
        logger.error(msg)
        return msg
```

### Step 3: Update Documentation

1. Add the tool to `docs/03-mcp-tools.md` with full API reference
2. Update the tool overview table in that document
3. Add examples of typical usage

### Step 4: Test

```bash
# Activate environment
source .venv/bin/activate

# Test the MCP server starts
python core/mcp_server.py

# Verify tool appears in tools/list
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python core/mcp_server.py
```

## Adding a New Subsystem

If a tool needs significant new functionality (like screen capture needed `vision_qa.py`), create a new module:

### Step 1: Create the Module

```python
"""New subsystem — brief description.

Detailed description of what this module does and why it exists.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NewSubsystem:
    """Manages [responsibility]."""

    def __init__(self, config_param: str) -> None:
        self.config_param = config_param
        logger.info("NewSubsystem initialized: %s", config_param)

    async def do_action(self, param: str) -> dict[str, Any]:
        """Perform an action.

        Args:
            param: Description.

        Returns:
            Dict with results.
        """
        logger.info("do_action → %s", param)
        # Implementation
        return {"status": "success", "result": "..."}
```

### Step 2: Integrate with MCP Server

```python
# In mcp_server.py, add at module level
from core.new_subsystem import NewSubsystem

new_sub = NewSubsystem(config_param=os.environ.get("NEW_PARAM", "default"))

# In tool function
@mcp.tool()
async def use_new_subsystem(param: str) -> str:
    """Tool that uses the new subsystem."""
    result = await new_sub.do_action(param)
    return str(result)
```

### Step 3: Update requirements.txt

If the new subsystem needs new dependencies, add them:

```
# Existing
mss>=9.0.0
Pillow>=10.0.0

# New
new-dependency>=1.0.0
```

## Architecture Principles

### 1. Safety First

- **Path traversal protection:** All file operations validate paths against project root
- **Timeout enforcement:** Every Godot process has a hard timeout
- **Input validation:** Pydantic schemas reject invalid inputs before they reach subsystems
- **No shell injection:** Use `asyncio.create_subprocess_exec` with argument arrays, not `shell=True`

### 2. Stateless Operations

- Each tool call is independent
- No shared state between operations
- No persistent Godot process (by default)
- Easy to reason about, test, and debug

### 3. LLM-Friendly Output

- Truncate long outputs (console logs, Base64 data)
- Use structured text for complex responses
- Include actionable error messages
- Return confirmation with byte counts, durations, etc.

### 4. Extensibility

- New tools are added by defining a Pydantic model + async function
- New subsystems are separate modules imported by the MCP server
- No architectural changes needed for new capabilities

## Testing

### Manual Testing

```bash
# Start the server
source .venv/bin/activate
python core/mcp_server.py

# Send JSON-RPC requests
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python core/mcp_server.py
```

### Automated Testing (Planned)

Future versions will include:
- Unit tests for each subsystem
- Integration tests for tool functions
- MCP protocol compliance tests

## Common Patterns

### Error Handling

```python
# Pattern: Return error string, don't raise
try:
    result = dangerous_operation()
    return f"OK: {result}"
except SpecificError as exc:
    return f"ERROR: {exc}"
except Exception as exc:
    logger.error("Unexpected: %s", exc, exc_info=True)
    return f"ERROR: Unexpected failure — {exc}"
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# At function entry
logger.info("function_name → param1=%s param2=%d", p1, p2)

# On success
logger.info("function_name completed: result=%s", result)

# On error
logger.error("function_name failed: %s", error)
```

### Async Subprocess

```python
# Pattern: Async with timeout and hard kill
proc = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
try:
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
except asyncio.TimeoutError:
    proc.kill()
    await proc.wait()
    # Handle timeout
```
