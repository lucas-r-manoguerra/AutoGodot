# AutoGodot — Documentation

This directory contains the complete technical documentation for the AutoGodot project.

## Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| [01-architecture.md](./01-architecture.md) | System architecture, component diagram, design philosophy | Everyone |
| [02-reference-analysis.md](./02-reference-analysis.md) | Analysis of reference MCP-Godot projects and our design choices | Contributors, architects |
| [03-mcp-tools.md](./03-mcp-tools.md) | Detailed documentation of every MCP tool (inputs, outputs, behavior) | AI agents, developers |
| [04-setup-guide.md](./04-setup-guide.md) | Step-by-step installation and configuration | End users |
| [05-godot-communication.md](./05-godot-communication.md) | How the framework communicates with Godot (subprocess, headless, etc.) | Contributors |
| [06-visual-qa.md](./06-visual-qa.md) | Screen capture system and visual QA pipeline | Contributors, AI agents |
| [07-development-guide.md](./07-development-guide.md) | Contributing, coding standards, and extension patterns | Contributors |

## Quick Reference

**What is this?** A Python-based MCP server that lets AI agents (Claude Desktop, VS Code, etc.) autonomously program, design scenes, and run visual QA on Godot 4.7 games.

**How does it work?** The MCP server exposes three tools over stdio transport. AI agents call these tools to write game files, launch Godot processes, and capture screenshots for visual verification.

**What makes it different?** See [02-reference-analysis.md](./02-reference-analysis.md) for a detailed comparison with existing MCP-Godot projects.

## Reading Order

For new contributors:
1. Start with [01-architecture.md](./01-architecture.md) to understand the big picture
2. Read [02-reference-analysis.md](./02-reference-analysis.md) to understand why we made certain design choices
3. Then read [03-mcp-tools.md](./03-mcp-tools.md) for the tool API reference
4. Follow [04-setup-guide.md](./04-setup-guide.md) to get it running locally

For AI agents using the tools:
1. Read [03-mcp-tools.md](./03-mcp-tools.md) for the complete tool API
2. Read [06-visual-qa.md](./06-visual-qa.md) for visual QA workflow
