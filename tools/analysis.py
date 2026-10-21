"""check_syntax catches syntax errors without running the code.
 outline gives a cheap map of classes and functions with line numbers, so June can read only the lines it needs."""

import ast

from .common import safe, tool, S

MAX_OUTLINE_LINES = 200


def _load(path):
    """Return (source, error). error is None on success."""
    p = safe(path)   # raises ValueError if outside workspace
    if not p.exists():
        return None, f"ERROR: path not found: {path}"
    if not p.is_file():
        return None, f"ERROR: not a file: {path}"
    try:
        return p.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        return None, f"ERROR: {path} is not a UTF-8 text file"


def check_syntax(path):
    source, err = _load(path)
    if err:
        return err
    try:
        ast.parse(source, filename=path)
    except SyntaxError as e:
        text = (e.text or "").strip()
        msg = f"SYNTAX ERROR in {path}, line {e.lineno}, col {e.offset}: {e.msg}"
        return msg + (f"\n  {text}" if text else "")
    except ValueError as e:
        return f"ERROR: {e}"
    return f"OK: {path} has no syntax errors"


def _args(node):
    try:
        return ast.unparse(node.args)
    except Exception:
        return "..."


def _walk(body, depth, out):
    pad = "  " * depth
    for node in body:
        if isinstance(node, ast.ClassDef):
            out.append(f"{pad}class {node.name} (lines {node.lineno}-{node.end_lineno})")
            _walk(node.body, depth + 1, out)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kw = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            out.append(
                f"{pad}{kw} {node.name}({_args(node)}) "
                f"(lines {node.lineno}-{node.end_lineno})"
            )


def outline(path):
    source, err = _load(path)
    if err:
        return err
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        return f"ERROR: cannot outline, syntax error at line {e.lineno}: {e.msg}"
    out = []
    _walk(tree.body, 0, out)
    if not out:
        return "(no classes or functions found)"
    if len(out) > MAX_OUTLINE_LINES:
        extra = len(out) - MAX_OUTLINE_LINES
        out = out[:MAX_OUTLINE_LINES] + [f"[...{extra} more entries not shown]"]
    return "\n".join(out)


SCHEMAS = [
    tool(
        "check_syntax",
        "Check a Python file for syntax errors without running it.",
        {"path": S},
        ["path"],
    ),
    tool(
        "outline",
        "List classes and functions of a Python file with line numbers. "
        "Use it before read_file to find what to read.",
        {"path": S},
        ["path"],
    ),
]