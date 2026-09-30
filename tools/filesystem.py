from .common import safe, tool, S

SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def read_file(path, limit=20000):
    text = safe(path).read_text(encoding="utf-8")
    if len(text) > limit:
        text = text[:limit] + f"\n[...truncated, file is {len(text)} chars]"
    return text


def write_file(path, content):
    p = safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Successfully wrote to {path}"


def list_dir(path="."):
    p = safe(path)
    items = sorted(p.iterdir())
    return "\n".join(
        i.name + ("/" if i.is_dir() else "")
        for i in items
        if i.name not in SKIP
    ) or "(empty)"


def edit_file(path, old, new):
    p = safe(path)
    text = p.read_text(encoding="utf-8")
    n = text.count(old)
    if n != 1:
        return f"ERROR: 'old' found {n} times; must be exactly 1."
    p.write_text(text.replace(old, new), encoding="utf-8")
    return f"Edited {path}"


SCHEMAS = [
    tool(
        "list_dir",
        "List files and folders in a workspace directory. "
        "Use this first to explore the project.",
        {"path": S},
        [],
    ),
    tool(
        "read_file",
        "Read a text file from the workspace.",
        {"path": S},
        ["path"],
    ),
    tool(
        "write_file",
        "Create a new file or fully overwrite an existing one. "
        "To change part of an existing file, use edit_file instead.",
        {"path": S, "content": S},
        ["path", "content"],
    ),
    tool(
        "edit_file",
        "Replace one exact snippet in an existing file. 'old' must "
        "appear exactly once; include surrounding lines to make it "
        "unique. Prefer this over write_file for changes.",
        {"path": S, "old": S, "new": S},
        ["path", "old", "new"],
    ),
]
