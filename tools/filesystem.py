from .common import safe, tool, trunc, S, SKIP


def _line_arg(value, name):
    """Return (int_or_None, error_or_None)."""
    if value is None:
        return None, None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None, f"ERROR: {name} must be an integer, got {value!r}"
    if n < 1:
        return None, f"ERROR: {name} must be >= 1 (lines are 1-based), got {n}"
    return n, None


def read_file(path, start=None, end=None):
    start, err = _line_arg(start, "start")
    if err:
        return err
    end, err = _line_arg(end, "end")
    if err:
        return err
    if start is not None and end is not None and start > end:
        return f"ERROR: start ({start}) is greater than end ({end})"

    p = safe(path)  # may raise ValueError (path guard) - intentionally not caught
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"ERROR: {e}"

    lines = text.splitlines()
    total = len(lines)
    if total == 0:
        return "[empty file]"

    first = start if start is not None else 1
    last = min(end, total) if end is not None else total

    if first > total:
        return f"ERROR: start ({first}) is past the end of the file, which has {total} lines"

    selected = lines[first - 1:last]
    header = f"[lines {first}-{last} of {total}]"
    body = "\n".join(
        f"{n}: {line}" for n, line in enumerate(selected, start=first)
    )
    return trunc(f"{header}\n{body}")


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
        "Read a text file. Optional start/end (1-based, inclusive) read a line range. "
        "Output lines are prefixed 'N: '; that prefix is NOT part of the file.",
        {
            "path": S,
            "start": {"type": "integer", "description": "first line (1-based)"},
            "end": {"type": "integer", "description": "last line (inclusive)"},
        },
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