import subprocess

from .common import safe, tool, trunc, S

GIT_TIMEOUT = 30
WORKDIR = None   # None = current folder. Tests set this to a temp repo.

def _git(*args):
    """Run git. Returns (exit_code, combined_output)."""
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
            stdin=subprocess.DEVNULL,
            env={**__import__("os").environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except FileNotFoundError:
        return 127, "git is not installed or not on PATH"
    except subprocess.TimeoutExpired:
        return 124, f"git timed out after {GIT_TIMEOUT}s"
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out


def _result(code, out):
    """Format a result: plain text on success, ERROR prefix on failure."""
    out = trunc(out) if out else "(no output)"
    return out if code == 0 else f"ERROR (exit {code}): {out}"

def git_status():
    return _result(*_git("status", "--short", "--branch"))


def git_log(n=10):
    try:
        n = max(1, min(int(n), 20))
    except (TypeError, ValueError):
        n = 10
    return _result(*_git("log", "--oneline", "-n", str(n)))

def git_diff(path=None):
    args = ["diff"]
    if path:
        safe(path)           # path guard only (raises ValueError if outside workspace)
        args += ["--", path]
    code, out = _git(*args)
    if code == 0 and not out:
        return "No unstaged changes."
    return _result(code, out)

def git_commit(message):
    if not message or not str(message).strip():
        return "ERROR: commit message must not be empty"
    code, out = _git("add", "-A")
    if code != 0:
        return _result(code, out)
    code, out = _git("commit", "-m", str(message).strip())
    if code != 0 and "nothing to commit" in out.lower():
        return out
    return _result(code, out)

SCHEMAS = [
    tool(
        "git_status",
        "Show branch and changed/untracked files (short format).",
        {},
        [],
    ),
    tool(
        "git_diff",
        "Show unstaged changes, optionally for one path. New untracked files "
        "are not shown here; see git_status.",
        {"path": {"type": "string", "description": "optional file or folder"}},
        [],
    ),
    tool(
        "git_log",
        "Show recent commits, one per line (max 20).",
        {"n": {"type": "integer", "description": "number of commits, default 10"}},
        [],
    ),
    tool(
        "git_commit",
        "Stage all changes and commit them. Only commit after tests pass.",
        {"message": S},
        ["message"],
    ),
]