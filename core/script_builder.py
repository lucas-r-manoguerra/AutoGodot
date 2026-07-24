"""
Script Builder — Structured GDScript manipulation
==================================================
Provides read/create/modify operations on .gd files using a structured
JSON representation instead of raw text.

Tools exposed:
  - read       : Parse a .gd into structured JSON
  - create     : Build a .gd from a JSON definition
  - modify     : Apply surgical operations to an existing .gd
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from gdtoolkit.parser import parser as gd_parser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled regex patterns for parsing GDScript (used in modify operations)
# ---------------------------------------------------------------------------

_RE_EXTENDS = re.compile(r"^extends\s+(\w+)", re.MULTILINE)
_RE_CLASS_NAME = re.compile(r"^class_name\s+(\w+)", re.MULTILINE)
_RE_SIGNAL = re.compile(r"^signal\s+(\w+)", re.MULTILINE)
_RE_VARIABLE = re.compile(
    r"^(?P<export>@export\s+)?var\s+(?P<name>\w+)"
    r"(?:\s*:\s*(?P<type>\w+))?"
    r"(?:\s*=\s*(?P<value>.+))?",
    re.MULTILINE,
)
_RE_FUNC_START = re.compile(r"^func\s+(\w+)\s*\(([^)]*)\)\s*:", re.MULTILINE)
_RE_FUNC_BODY = re.compile(
    r"^func\s+\w+\s*\([^)]*\)\s*:\s*\n(?P<body>(?:\t.*\n?)*)",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Template strings for generation
# ---------------------------------------------------------------------------

TPL_EXTENDS = "extends {extends}"
TPL_CLASS_NAME = "class_name {class_name}"
TPL_SIGNAL = "signal {name}"
TPL_VAR_EXPORT = "@export var {name}: {type} = {value}"
TPL_VAR_TYPED = "var {name}: {type} = {value}"
TPL_VAR_UNTYPED = "var {name} = {value}"
TPL_FUNC_HEADER = "func {name}({args}):"
TPL_FUNC_HEADER_RETURN = "func {name}({args}) -> {return_type}:"

# Valid modify actions
VALID_ACTIONS = {
    "add_signal",
    "remove_signal",
    "add_variable",
    "remove_variable",
    "add_function",
    "remove_function",
    "replace_function_body",
    "set_extends",
    "set_class_name",
}


class ScriptBuilder:
    """Structured read/create/modify for GDScript (.gd) files."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.resolve()
        logger.info("ScriptBuilder initialized (project: %s)", self.project_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read(self, script_path: str) -> dict[str, Any] | str:
        """Parse a .gd file and return structured JSON.

        Args:
            script_path: Relative path to the .gd inside the project.

        Returns:
            Dict with keys: extends, class_name, signals, variables, functions, metadata.
            On error: returns "ERROR: ..." string.
        """
        target = self._validate_path(script_path)
        if isinstance(target, str):
            return target

        if not target.exists():
            return f"ERROR: Script file not found: {script_path}"

        try:
            content = target.read_text()
            return self._parse_script(content, script_path)
        except Exception as exc:
            msg = f"ERROR reading script {script_path}: {exc}"
            logger.error(msg)
            return msg

    def create(self, script_path: str, definition: dict[str, Any]) -> str:
        """Create a .gd file from a JSON definition.

        Args:
            script_path: Relative path where the .gd will be written.
            definition: Script dict with extends, class_name, signals, variables, functions.

        Returns:
            "OK: ..." message with counts, or "ERROR: ..." string.
        """
        target = self._validate_path(script_path)
        if isinstance(target, str):
            return target

        extends = definition.get("extends")
        if not extends:
            return "ERROR: Definition must include 'extends' field"

        try:
            content = self._generate_script(definition)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

            signals = definition.get("signals", [])
            variables = definition.get("variables", [])
            functions = definition.get("functions", [])

            msg = f"OK: Created script {script_path} ({len(signals)} signals, {len(variables)} variables, {len(functions)} functions)"
            logger.info(msg)
            return msg

        except Exception as exc:
            msg = f"ERROR creating script {script_path}: {exc}"
            logger.error(msg)
            return msg

    def modify(self, script_path: str, operations: list[dict[str, Any]]) -> str:
        """Apply surgical modifications to an existing .gd file.

        Args:
            script_path: Relative path to the .gd to modify.
            operations: List of operation dicts.

        Returns:
            "OK: ..." message with change summary, or "ERROR: ..." string.
        """
        target = self._validate_path(script_path)
        if isinstance(target, str):
            return target

        if not target.exists():
            return f"ERROR: Script file not found: {script_path}"

        try:
            content = target.read_text()
            changes: list[str] = []

            for op in operations:
                action = op.get("action", "")
                if action not in VALID_ACTIONS:
                    return f"ERROR: Unknown action: {action}"

                content, change = self._apply_operation(content, op)
                if change:
                    changes.append(change)

            target.write_text(content)

            summary = "; ".join(changes) if changes else "no changes"
            msg = f"OK: Modified script {script_path} — {summary}"
            logger.info(msg)
            return msg

        except Exception as exc:
            msg = f"ERROR modifying script {script_path}: {exc}"
            logger.error(msg)
            return msg

    # ------------------------------------------------------------------
    # Path validation (identical to SceneBuilder)
    # ------------------------------------------------------------------

    def _validate_path(self, script_path: str) -> Path | str:
        """Validate and resolve a script path. Returns Path or ERROR string."""
        if ".." in script_path or script_path.startswith("/"):
            return f"ERROR: Path traversal not allowed: {script_path}"

        target = self.project_dir / script_path
        try:
            target = target.resolve()
            if not str(target).startswith(str(self.project_dir)):
                return f"ERROR: Path escapes project directory: {script_path}"
        except Exception:
            return f"ERROR: Invalid path: {script_path}"

        return target

    # ------------------------------------------------------------------
    # Parsing (read) — using gdtoolkit
    # ------------------------------------------------------------------

    def _parse_script(self, content: str, script_path: str) -> dict[str, Any]:
        """Parse GDScript content into structured dict using gdtoolkit."""
        result: dict[str, Any] = {
            "extends": "",
            "class_name": "",
            "signals": [],
            "variables": [],
            "functions": [],
            "metadata": {
                "lines": len(content.split("\n")),
                "path": script_path,
            },
        }

        try:
            tree = gd_parser.parse(content)
        except Exception as exc:
            logger.warning("gdtoolkit parse failed, falling back to regex: %s", exc)
            return self._parse_script_regex(content, script_path)

        # Track if previous node was an annotation
        prev_was_annotation = False

        for child in tree.children:
            if not hasattr(child, "data"):
                continue

            if child.data == "extends_stmt":
                result["extends"] = self._extract_token(child, 0)

            elif child.data == "classname_stmt":
                result["class_name"] = self._extract_token(child, 0)

            elif child.data == "signal_stmt":
                result["signals"].append(self._extract_token(child, 0))

            elif child.data == "annotation":
                prev_was_annotation = True

            elif child.data == "class_var_stmt":
                var = self._extract_variable(child)
                if prev_was_annotation:
                    var["export"] = True
                    prev_was_annotation = False
                else:
                    var["export"] = False
                result["variables"].append(var)

            elif child.data == "func_def":
                func = self._extract_function(child)
                result["functions"].append(func)
                prev_was_annotation = False

            else:
                prev_was_annotation = False

        return result

    def _extract_token(self, node: Any, index: int) -> str:
        """Extract a token value from a tree node."""
        if index < len(node.children):
            child = node.children[index]
            if hasattr(child, "value"):
                return child.value
            return str(child)
        return ""

    def _extract_variable(self, node: Any) -> dict[str, Any]:
        """Extract variable information from a class_var_stmt node."""
        var_info: dict[str, Any] = {"name": "", "export": False}

        # Navigate to the inner var node
        if node.children:
            inner = node.children[0]
            if hasattr(inner, "children"):
                # First child is the variable name
                if inner.children:
                    var_info["name"] = self._extract_token(inner, 0)

                # Look for type hint and value
                for child in inner.children[1:]:
                    if hasattr(child, "type") and child.type == "TYPE_HINT":
                        var_info["type"] = child.value
                    elif hasattr(child, "data") and child.data == "expr":
                        # Extract the value expression
                        var_info["value"] = self._extract_expr(child)

        return var_info

    def _extract_expr(self, node: Any) -> str:
        """Extract expression value from a tree node."""
        if hasattr(node, "children") and node.children:
            child = node.children[0]
            if hasattr(child, "value"):
                return child.value
            elif hasattr(child, "data"):
                return self._extract_expr(child)
        return ""

    def _extract_function(self, node: Any) -> dict[str, Any]:
        """Extract function information from a func_def node."""
        func_info: dict[str, Any] = {
            "name": "",
            "args": "",
            "body": [],
        }

        if not node.children:
            return func_info

        # First child is func_header
        header = node.children[0]
        if hasattr(header, "children") and header.children:
            # First token is function name
            func_info["name"] = self._extract_token(header, 0)

            # Second child is func_args
            if len(header.children) > 1:
                args_tree = header.children[1]
                func_info["args"] = self._extract_func_args(args_tree)

            # Check for return type (third child if present)
            if len(header.children) > 2:
                return_type = header.children[2]
                if hasattr(return_type, "value"):
                    func_info["return_type"] = return_type.value

        # Remaining children are body statements
        body_lines: list[str] = []
        for body_node in node.children[1:]:
            line = self._extract_body_line(body_node)
            if line:
                body_lines.append(line)

        func_info["body"] = body_lines
        return func_info

    def _extract_func_args(self, node: Any) -> str:
        """Extract function arguments from func_args node."""
        args: list[str] = []

        if hasattr(node, "children"):
            for arg in node.children:
                if hasattr(arg, "data") and arg.data == "func_arg_typed":
                    # Typed argument: name: type
                    if hasattr(arg, "children") and len(arg.children) >= 2:
                        name = self._extract_token(arg, 0)
                        type_hint = arg.children[1]
                        if hasattr(type_hint, "value"):
                            args.append(f"{name}: {type_hint.value}")
                elif hasattr(arg, "data") and arg.data == "func_arg":
                    # Untyped argument
                    args.append(self._extract_token(arg, 0))

        return ", ".join(args)

    def _extract_body_line(self, node: Any) -> str:
        """Extract a body line from a statement node."""
        if hasattr(node, "data"):
            if node.data == "pass_stmt":
                return "\tpass"
            elif node.data == "expr_stmt":
                return "\t" + self._extract_expr(node)
            elif node.data == "return_stmt":
                return "\treturn " + self._extract_expr(node)
            elif node.data == "if_stmt":
                return self._extract_if_stmt(node)
            elif node.data == "for_stmt":
                return self._extract_for_stmt(node)
            elif node.data == "while_stmt":
                return self._extract_while_stmt(node)
        return ""

    def _extract_if_stmt(self, node: Any) -> str:
        """Extract if statement."""
        if hasattr(node, "children") and node.children:
            condition = self._extract_expr(node.children[0])
            return f"\tif {condition}:"
        return "\tif:"

    def _extract_for_stmt(self, node: Any) -> str:
        """Extract for statement."""
        if hasattr(node, "children") and node.children:
            return f"\tfor {self._extract_expr(node.children[0])}:"
        return "\tfor:"

    def _extract_while_stmt(self, node: Any) -> str:
        """Extract while statement."""
        if hasattr(node, "children") and node.children:
            return f"\twhile {self._extract_expr(node.children[0])}:"
        return "\twhile:"

    # ------------------------------------------------------------------
    # Parsing fallback — regex (used when gdtoolkit fails)
    # ------------------------------------------------------------------

    def _parse_script_regex(self, content: str, script_path: str) -> dict[str, Any]:
        """Parse GDScript content using regex (fallback)."""
        result: dict[str, Any] = {
            "extends": "",
            "class_name": "",
            "signals": [],
            "variables": [],
            "functions": [],
            "metadata": {
                "lines": len(content.split("\n")),
                "path": script_path,
            },
        }

        # Parse extends
        m = _RE_EXTENDS.search(content)
        if m:
            result["extends"] = m.group(1)

        # Parse class_name
        m = _RE_CLASS_NAME.search(content)
        if m:
            result["class_name"] = m.group(1)

        # Parse signals
        for m in _RE_SIGNAL.finditer(content):
            result["signals"].append(m.group(1))

        # Parse variables
        for m in _RE_VARIABLE.finditer(content):
            var: dict[str, Any] = {
                "name": m.group("name"),
                "export": m.group("export") is not None,
            }
            if m.group("type"):
                var["type"] = m.group("type")
            if m.group("value"):
                var["value"] = m.group("value").strip()
            result["variables"].append(var)

        # Parse functions
        func_starts = list(_RE_FUNC_START.finditer(content))
        for idx, fm in enumerate(func_starts):
            func_name = fm.group(1)
            func_args = fm.group(2).strip()

            # Find body: from end of func line to next func or EOF
            body_start = content.find("\n", fm.end())
            if body_start == -1:
                body_start = fm.end()

            if idx + 1 < len(func_starts):
                body_end = func_starts[idx + 1].start()
            else:
                body_end = len(content)

            body_text = content[body_start:body_end]
            body_lines = [line for line in body_text.split("\n") if line.strip()]

            result["functions"].append(
                {
                    "name": func_name,
                    "args": func_args,
                    "body": body_lines,
                }
            )

        return result

    # ------------------------------------------------------------------
    # Generation (create)
    # ------------------------------------------------------------------

    def _generate_script(self, definition: dict[str, Any]) -> str:
        """Generate GDScript content from structured definition."""
        sections: list[str] = []

        # 1. extends (required)
        extends = definition.get("extends", "Node")
        sections.append(TPL_EXTENDS.format(extends=extends))

        # 2. class_name (optional)
        class_name = definition.get("class_name")
        if class_name:
            sections.append(TPL_CLASS_NAME.format(class_name=class_name))

        # 3. signals (optional)
        signals = definition.get("signals", [])
        if signals:
            signal_lines = []
            for sig in signals:
                if isinstance(sig, dict):
                    name = sig["name"]
                    params = sig.get("parameters", [])
                    if params:
                        param_str = ", ".join(
                            f"{p['name']}: {p['type']}" for p in params
                        )
                        signal_lines.append(f"signal {name}({param_str})")
                    else:
                        signal_lines.append(f"signal {name}")
                else:
                    signal_lines.append(f"signal {sig}")
            sections.append("\n".join(signal_lines))

        # 4. exported variables (optional)
        variables = definition.get("variables", [])
        export_vars = [v for v in variables if v.get("export")]
        regular_vars = [v for v in variables if not v.get("export")]

        if export_vars:
            export_lines = [self._gen_var_line(v, exported=True) for v in export_vars]
            sections.append("\n".join(export_lines))

        # 5. regular variables (optional)
        if regular_vars:
            var_lines = [self._gen_var_line(v, exported=False) for v in regular_vars]
            sections.append("\n".join(var_lines))

        # 6. functions (optional)
        functions = definition.get("functions", [])
        if functions:
            func_blocks = []
            for func in functions:
                block = self._gen_func_block(func)
                func_blocks.append(block)
            sections.append("\n\n".join(func_blocks))

        return "\n\n".join(sections) + "\n"

    def _gen_var_line(self, var: dict[str, Any], exported: bool = False) -> str:
        """Generate a single variable declaration line."""
        name = var["name"]
        var_type = var.get("type")
        value = var.get("value")

        if exported:
            if var_type and value:
                return f"@export var {name}: {var_type} = {value}"
            elif var_type:
                return f"@export var {name}: {var_type}"
            else:
                return f"@export var {name}"
        else:
            if var_type and value:
                return f"var {name}: {var_type} = {value}"
            elif var_type:
                return f"var {name}: {var_type}"
            elif value:
                return f"var {name} = {value}"
            else:
                return f"var {name}"

    def _gen_func_block(self, func: dict[str, Any]) -> str:
        """Generate a function block."""
        name = func["name"]
        args = func.get("args", "")
        return_type = func.get("return_type")
        body = func.get("body", [])

        if return_type:
            header = TPL_FUNC_HEADER_RETURN.format(
                name=name, args=args, return_type=return_type
            )
        else:
            header = TPL_FUNC_HEADER.format(name=name, args=args)

        if body:
            body_text = "\n".join(body)
            return f"{header}\n{body_text}"
        else:
            return f"{header}\n\tpass"

    # ------------------------------------------------------------------
    # Modification (modify)
    # ------------------------------------------------------------------

    def _apply_operation(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        """Apply a single operation to content. Returns (new_content, change_desc)."""
        action = op["action"]

        if action == "add_signal":
            return self._op_add_signal(content, op)
        elif action == "remove_signal":
            return self._op_remove_signal(content, op)
        elif action == "add_variable":
            return self._op_add_variable(content, op)
        elif action == "remove_variable":
            return self._op_remove_variable(content, op)
        elif action == "add_function":
            return self._op_add_function(content, op)
        elif action == "remove_function":
            return self._op_remove_function(content, op)
        elif action == "replace_function_body":
            return self._op_replace_function_body(content, op)
        elif action == "set_extends":
            return self._op_set_extends(content, op)
        elif action == "set_class_name":
            return self._op_set_class_name(content, op)
        else:
            return content, ""

    def _op_add_signal(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        name = op["name"]
        line = f"signal {name}"

        # Find where signals section ends or insert after last signal
        last_signal = None
        for m in _RE_SIGNAL.finditer(content):
            last_signal = m

        if last_signal:
            # Insert after last signal
            end = last_signal.end()
            # Find end of line
            nl = content.find("\n", end)
            if nl == -1:
                nl = len(content)
            new_content = content[: nl + 1] + line + content[nl:]
        else:
            # Insert after extends/class_name or at top
            m = _RE_EXTENDS.search(content) or _RE_CLASS_NAME.search(content)
            if m:
                end = m.end()
                nl = content.find("\n", end)
                if nl == -1:
                    nl = len(content)
                new_content = content[: nl + 1] + "\n" + line + content[nl:]
            else:
                new_content = line + "\n" + content

        return new_content, f"added signal '{name}'"

    def _op_remove_signal(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        name = op["name"]
        pattern = re.compile(rf"^signal\s+{re.escape(name)}\s*$", re.MULTILINE)
        new_content = pattern.sub("", content)
        # Clean up double blank lines
        new_content = re.sub(r"\n{3,}", "\n\n", new_content)
        return new_content, f"removed signal '{name}'"

    def _op_add_variable(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        name = op["name"]
        var_type = op.get("type")
        value = op.get("value")
        exported = op.get("export", False)

        var: dict[str, Any] = {"name": name}
        if var_type:
            var["type"] = var_type
        if value:
            var["value"] = value

        line = self._gen_var_line(var, exported=exported)

        # Find where variables section ends
        last_var = None
        for m in _RE_VARIABLE.finditer(content):
            last_var = m

        if last_var:
            end = last_var.end()
            nl = content.find("\n", end)
            if nl == -1:
                nl = len(content)
            new_content = content[: nl + 1] + line + content[nl:]
        else:
            # Insert after signals or extends/class_name
            m = (
                _RE_SIGNAL.search(content)
                or _RE_CLASS_NAME.search(content)
                or _RE_EXTENDS.search(content)
            )
            if m:
                end = m.end()
                nl = content.find("\n", end)
                if nl == -1:
                    nl = len(content)
                new_content = content[: nl + 1] + "\n" + line + content[nl:]
            else:
                new_content = line + "\n" + content

        return new_content, f"added variable '{name}'"

    def _op_remove_variable(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        name = op["name"]
        pattern = re.compile(
            r"^(?:@export\s+)?var\s+" + re.escape(name) + r"[^\n]*$",
            re.MULTILINE,
        )
        new_content = pattern.sub("", content)
        new_content = re.sub(r"\n{3,}", "\n\n", new_content)
        return new_content, f"removed variable '{name}'"

    def _op_add_function(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        func: dict[str, Any] = {
            "name": op["name"],
            "args": op.get("args", ""),
        }
        if "return_type" in op:
            func["return_type"] = op["return_type"]
        func["body"] = op.get("body", ["\tpass"])

        block = self._gen_func_block(func)

        # Append at end of file
        if content.rstrip():
            new_content = content.rstrip() + "\n\n" + block + "\n"
        else:
            new_content = block + "\n"

        return new_content, f"added function '{op['name']}'"

    def _op_remove_function(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        name = op["name"]
        # Find function start
        m = _RE_FUNC_START.search(content)
        while m and m.group(1) != name:
            m = _RE_FUNC_START.search(content, m.end())

        if not m:
            return content, ""

        start = m.start()
        # Find end: next func or EOF
        next_func = _RE_FUNC_START.search(content, m.end())
        end = next_func.start() if next_func else len(content)

        # Remove the function block and trailing blank lines
        new_content = content[:start] + content[end:]
        new_content = re.sub(r"\n{3,}", "\n\n", new_content)
        return new_content, f"removed function '{name}'"

    def _op_replace_function_body(
        self, content: str, op: dict[str, Any]
    ) -> tuple[str, str]:
        name = op["name"]
        new_body = op.get("body", ["\tpass"])

        # Find function
        m = _RE_FUNC_START.search(content)
        while m and m.group(1) != name:
            m = _RE_FUNC_START.search(content, m.end())

        if not m:
            return content, ""

        # Find body start (after the func line)
        body_start = content.find("\n", m.end())
        if body_start == -1:
            return content, ""

        # Find end: next func or EOF
        next_func = _RE_FUNC_START.search(content, m.end())
        body_end = next_func.start() if next_func else len(content)

        # Build new function
        func_header = content[m.start() : body_start]
        new_body_text = "\n".join(new_body)
        new_func = f"{func_header}\n{new_body_text}\n"

        new_content = content[: m.start()] + new_func + content[body_end:]
        return new_content, f"replaced body of '{name}'"

    def _op_set_extends(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        value = op["value"]
        new_line = f"extends {value}"

        m = _RE_EXTENDS.search(content)
        if m:
            new_content = content[: m.start()] + new_line + content[m.end() :]
        else:
            new_content = new_line + "\n" + content

        return new_content, f"set extends to '{value}'"

    def _op_set_class_name(self, content: str, op: dict[str, Any]) -> tuple[str, str]:
        value = op["value"]
        new_line = f"class_name {value}"

        m = _RE_CLASS_NAME.search(content)
        if m:
            new_content = content[: m.start()] + new_line + content[m.end() :]
        else:
            # Add after extends
            m2 = _RE_EXTENDS.search(content)
            if m2:
                end = m2.end()
                nl = content.find("\n", end)
                if nl == -1:
                    nl = len(content)
                new_content = content[: nl + 1] + new_line + content[nl:]
            else:
                new_content = new_line + "\n" + content

        return new_content, f"set class_name to '{value}'"
