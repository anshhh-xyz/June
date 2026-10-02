import fnmatch
import os
import re
from pathlib import Path

from .common import safe, tool, S, SKIP

MAX_RESULTS = 50          # matches / files returned per call
MAX_LINE_LEN = 200        # long lines are cut so one minified file can't flood the output
MAX_FILE_BYTES = 1_000_000  # skip files bigger than ~1 MB

def _iter_files(base: Path):
    """Yield every file under base, skipping SKIP folders. base may be a file."""
    if base.is_file():
        yield base
        return
    for root, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        for name in sorted(files):
            yield Path(root) / name


def _rel(p: Path) -> str:
    """Path relative to the working folder, with forward slashes."""
    try:
        return p.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return p.as_posix()

def _is_text(p: Path) -> bool:
    try:
        if p.stat().st_size > MAX_FILE_BYTES:
            return False
        with open(p, "rb") as f:
            return b"\x00" not in f.read(1024)
    except OSError:
        return False

def search_code(pattern, path="."):
    base = safe(path)
    if not base.exists():
        return f"ERROR: path not found: {path}"
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"ERROR: invalid regex {pattern!r}: {e}"

    results = []
    truncated = False
    for fp in _iter_files(base):
        if not _is_text(fp):
            continue
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                for n, line in enumerate(f, start=1):
                    line = line.rstrip("\r\n")
                    if rx.search(line):
                        if len(results) >= MAX_RESULTS:
                            truncated = True
                            break
                        text = line.strip()
                        if len(text) > MAX_LINE_LEN:
                            text = text[:MAX_LINE_LEN] + "..."
                        results.append(f"{_rel(fp)}:{n}: {text}")
        except OSError:
            continue
        if truncated:
            break

    if not results:
        return "No matches."
    out = "\n".join(results)
    if truncated:
        out += f"\n[truncated at {MAX_RESULTS} results; narrow the pattern or path]"
    return out

def find_files(pattern):
    base = safe(".")
    results = []
    truncated = False
    for fp in _iter_files(base):
        rel = _rel(fp)
        if fnmatch.fnmatch(fp.name, pattern) or fnmatch.fnmatch(rel, pattern):
            if len(results) >= MAX_RESULTS:
                truncated = True
                break
            results.append(rel)

    if not results:
        return "No matches."
    out = "\n".join(results)
    if truncated:
        out += f"\n[truncated at {MAX_RESULTS} results; use a more specific pattern]"
    return out

SCHEMAS = [
    tool(
        "search_code",
        "Regex search over text files. Returns 'path:line: text' lines (max 50). "
        "Use to locate code before reading it.",
        {
            "pattern": {"type": "string", "description": "regex to search for"},
            "path": {"type": "string", "description": "folder or file, default '.'"},
        },
        ["pattern"],
    ),
    tool(
        "find_files",
        "Find files by glob pattern, e.g. '*.py' or 'test_*'. Returns paths (max 50).",
        {"pattern": {"type": "string", "description": "glob pattern"}},
        ["pattern"],
    ),
]