# Reference Project Analysis

This document analyzes two established MCP-Godot projects and explains how their patterns inform our architecture.

## Projects Analyzed

| Project | Author | Language | Stars | Tools | Approach |
|---------|--------|----------|-------|-------|----------|
| [godot-mcp](https://github.com/Coding-Solo/godot-mcp) | Coding-Solo | TypeScript | ~4.9k | 14 | CLI + Headless GDScript |
| [Godot-MCP-Native](https://github.com/yurineko73/Godot-MCP-Native) | yurineko73 | GDScript | — | 155 | Pure GDScript in-editor |

---

## 1. godot-mcp (Coding-Solo)

### Architecture

```
AI Agent ↔ MCP Server (TypeScript/Node.js) ↔ Godot CLI
                                                 │
                                          godot_operations.gd (headless)
```

**Two-tier approach:**
- **Tier 1 (CLI):** Simple operations (`launch_editor`, `run_project`, `get_godot_version`) are executed directly via Node.js `child_process.spawn()` calling Godot CLI.
- **Tier 2 (Headless GDScript):** Complex operations (`create_scene`, `add_node`, `load_sprite`, `save_scene`) spawn Godot in headless mode with `--script godot_operations.gd <operation> <json_params>`.

### Key Patterns We Adopt

#### Pattern: Standardized Error Responses

```typescript
// From godot-mcp: every error includes actionable solutions
createErrorResponse(message, possibleSolutions[])
```

**Why it's good:** AI agents benefit from knowing not just *what* failed, but *how to fix it*. We adopt this pattern in our error responses.

**Our implementation:** Tool responses include structured error information with context for the LLM.

#### Pattern: Path Traversal Protection

```typescript
// Rejects paths containing ".."
validatePath(path)
// Validates class names with regex
validateClassName(name)  // /^[A-Za-z_][A-Za-z0-9_]*$/
```

**Why it's good:** AI agents can generate arbitrary file paths. Without validation, a prompt injection could write files outside the project.

**Our implementation:** `write_game_file` resolves the target path and verifies it starts with the project root.

#### Pattern: Process Isolation

Each complex operation spawns a fresh Godot process. No persistent connection.

**Why it's good:** No state corruption between operations. No plugin installation required. Simpler debugging.

**Our adoption:** We follow this same stateless approach. Each `run_godot_test` call is independent.

#### Pattern: Single GDScript Dispatcher

`godot_operations.gd` (~700 lines) is a single file with a `match` statement dispatching to operation functions.

**Tradeoff:** Simple to maintain but monolithic. For 14 tools this works fine. For 155+ tools it would be unwieldy.

### What We Don't Adopt

- **TypeScript/Node.js runtime:** We use Python for consistency with the MCP Python SDK and broader AI/ML ecosystem.
- **GDScript headless execution for file writes:** We write files directly from Python (simpler, no Godot process needed for plain text files).
- **camelCase/snake_case translation layer:** We use Python snake_case throughout, matching both MCP conventions and GDScript conventions.

---

## 2. Godot-MCP-Native (yurineko73)

### Architecture

```
AI Agent ↔ HTTP/JSON-RPC ↔ GDScript MCP Server (inside Godot editor)
                                    │
                             Godot Editor API
```

**Key difference:** The MCP server is a Godot editor plugin written entirely in GDScript. It runs inside the Godot process, giving direct access to the editor API.

### Key Patterns We Reference

#### Pattern: Tool Annotations

```gdscript
{
  "readOnlyHint": true,      # Tool doesn't modify state
  "destructiveHint": false,  # Tool won't destroy data
  "idempotentHint": true,    # Running twice = same result
  "openWorldHint": false     # Tool is sandboxed
}
```

**Why it's good:** MCP annotations help AI agents understand tool behavior and make better decisions about when to use them.

**Our adoption:** We'll add annotations to future tool definitions as our tool set grows.

#### Pattern: Bearer Token Authentication

For HTTP transport, tokens prevent unauthorized access.

**Why it's relevant:** Not needed for stdio (the server runs as a child process), but important if we ever add HTTP transport.

#### Pattern: Vibe Coding Mode

UI protection feature that requires explicit `allow_ui_focus=true` for tools that would steal editor focus.

**Why it's good:** Prevents AI from unexpectedly switching scenes, selecting nodes, or disrupting the developer's workflow.

**Our consideration:** Relevant for future editor integration features.

#### Pattern: Runtime Probe

An autoloaded `MCPRuntimeProbe` node injected into the running game enables:
- Live scene tree inspection
- Runtime node property modification
- Method calls on live nodes
- GDScript expression evaluation

**Why it's powerful:** This is the most sophisticated pattern in either project. It enables real-time game introspection without headless mode.

**Our consideration:** This is a high-value feature for future versions but requires significant complexity (autoload injection, debugger bridge, signal communication).

### What We Don't Adopt

- **Pure GDScript server:** Our server is Python, running on the host system. This means:
  - No Godot editor required to run the MCP server
  - No plugin installation per project
  - No GDScript dependency for the server itself
- **HTTP transport:** We use stdio for simplicity and universal MCP client compatibility.
- **155 tools:** We start with 3 focused tools and expand based on real usage patterns, not feature count.

---

## 3. Comparative Analysis

### Communication Models

| Aspect | godot-mcp | Godot-MCP-Native | AutoGodot |
|--------|-----------|------------------|-------------------|
| **MCP Server** | TypeScript (Node.js) | GDScript (in-editor) | Python (host) |
| **Transport** | stdio | HTTP (TCPServer) | stdio |
| **Godot Communication** | CLI + headless GDScript | Direct editor API | CLI subprocess |
| **Persistent Connection** | No | Yes (editor process) | No |
| **Requires Godot Running** | No | Yes (editor must be open) | No |
| **Plugin Installation** | No | Yes (addons/) | No |
| **External Runtime** | Node.js | None (pure GDScript) | Python |

### Tool Capabilities

| Category | godot-mcp | Godot-MCP-Native | AutoGodot |
|----------|-----------|------------------|-------------------|
| File Write | ✅ (via headless) | ✅ (direct API) | ✅ (direct Python) |
| Scene Create | ✅ | ✅ | — (planned) |
| Node Manipulation | ✅ | ✅ (20 tools) | — (planned) |
| Script Management | — | ✅ (15 tools) | — (planned) |
| Run Project | ✅ | ✅ | ✅ |
| Visual QA | — | ✅ (screenshot) | ✅ (capture + resize) |
| Runtime Introspection | — | ✅ (71 tools) | — (planned) |
| Editor Integration | ✅ (launch editor) | ✅ (full editor) | — (planned) |

### Safety Features

| Feature | godot-mcp | Godot-MCP-Native | AutoGodot |
|---------|-----------|------------------|-------------------|
| Path Traversal Protection | ✅ | ✅ | ✅ |
| Timeout Enforcement | ✅ | N/A (in-process) | ✅ |
| Hard Kill on Timeout | ✅ | N/A | ✅ |
| Input Validation | Regex | JSON Schema | Pydantic |
| Auth (HTTP) | N/A | Bearer Token | N/A (stdio) |
| Rate Limiting | N/A | ✅ | N/A (stdio) |
| Error with Solutions | ✅ | — | ✅ (planned) |

---

## 4. Design Decisions Based on Analysis

### Decision 1: Python over TypeScript

**Context:** godot-mcp uses TypeScript. Godot-MCP-Native uses GDScript.

**Decision:** Python.

**Rationale:**
- Official MCP Python SDK is mature and well-documented
- Python is the dominant language in AI/ML (the ecosystem our users work in)
- Easier for AI agents to modify/extend the server itself
- Rich library ecosystem (mss, Pillow, asyncio)

### Decision 2: stdio over HTTP

**Context:** godot-mcp uses stdio. Godot-MCP-Native uses HTTP.

**Decision:** stdio.

**Rationale:**
- Universal MCP client support (Claude Desktop, VS Code, OpenCode)
- No port management, no CORS, no auth needed
- Server runs as child process (natural security boundary)
- Simpler deployment (no server startup step)

### Decision 3: Stateless Subprocess over Persistent Connection

**Context:** Both reference projects use stateless approaches (godot-mcp spawns processes, Godot-MCP-Native runs in-editor but each tool call is independent).

**Decision:** Stateless subprocess.

**Rationale:**
- No state corruption between operations
- No Godot editor installation required to use the MCP server
- No plugin conflicts with existing project addons
- Simpler to test and debug
- Natural timeout enforcement (each process has a hard limit)

### Decision 4: Start Small, Expand Based on Usage

**Context:** godot-mcp has 14 tools. Godot-MCP-Native has 155 tools.

**Decision:** Start with 3 tools, expand based on real usage patterns.

**Rationale:**
- Fewer tools = simpler initial architecture
- Each tool gets more attention (testing, documentation, edge cases)
- Avoids building features nobody uses
- Easier for AI agents to learn the tool set
- Can always add more later without breaking existing tools

### Decision 5: Python File Writes over GDScript Headless

**Context:** godot-mcp writes files by spawning Godot headless with a GDScript. We write files directly from Python.

**Decision:** Direct Python file writes for text files.

**Rationale:**
- No Godot process needed for simple file creation
- Faster (no process spawn overhead)
- More reliable (no Godot startup errors for file operations)
- GDScript headless is only needed when you need Godot's API (scene manipulation, resource loading)

---

## 5. Patterns Worth Adopting in Future Versions

### From godot-mcp

1. **`createErrorResponse(message, solutions[])`** — Structured error responses with actionable fixes
2. **Class name validation** — Regex check before creating nodes
3. **UID management** — Godot 4.4+ UID support for resource references

### From Godot-MCP-Native

1. **Tool annotations** — `readOnlyHint`, `destructiveHint`, `idempotentHint` for AI decision-making
2. **Runtime Probe** — Autoloaded node for live game introspection
3. **Vibe Coding Mode** — UI protection to prevent AI from disrupting developer workflow
4. **Undo/Redo integration** — Proper undo support for scene modifications
5. **Tool state management** — Enable/disable individual tools per project

---

## 6. Summary

Both reference projects validate different architectural approaches:

- **godot-mcp** proves that a **stateless CLI-based approach** works well for 14 core tools with minimal setup.
- **Godot-MCP-Native** proves that a **deep editor integration** approach can scale to 155+ tools with sophisticated runtime introspection.

**AutoGodot** takes the middle path: Python-based, stdio transport, stateless subprocess execution, starting with 3 focused tools. This gives us:
- Simplicity for end users (one command setup)
- Reliability (hard timeouts, process isolation)
- Extensibility (can add tools without architectural changes)
- Foundation for future deep integration (editor plugin, runtime probe) when needed
