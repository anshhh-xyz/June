"""It runs the project’s tests and returns passed, return_code and output. It uses pytest if installed, otherwise unittest. 
It never uses shell=True. The 120s timeout means a hanging test can’t freeze June, and path is checked against the workspace 
guard."""


import importlib.util
import os
import subprocess
import sys

from .common import WORKSPACE, safe, tool, trunc

TEST_TIMEOUT = 120


def _has_pytest():
    return importlib.util.find_spec("pytest") is not None


def _as_text(x):
    if x is None:
        return ""
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="replace")
    return x


def run_tests(path=None):
    target = None
    if path:
        target = safe(path)   # raises ValueError if outside workspace
        if not target.exists():
            return {"passed": False, "return_code": -1,
                    "output": f"ERROR: path not found: {path}"}

    if _has_pytest():
        runner = "pytest"
        cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short",
               "-p", "no:cacheprovider"]
        if target:
            cmd.append(str(target))
    else:
        runner = "unittest"
        cmd = [sys.executable, "-m", "unittest", "discover"]
        if target:
            if target.is_file():
                cmd += ["-s", str(target.parent), "-p", target.name]
            else:
                cmd += ["-s", str(target)]

    try:
        r = subprocess.run(
            cmd,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=TEST_TIMEOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired as e:
        partial = _as_text(e.stdout) + _as_text(e.stderr)
        return {"runner": runner, "passed": False, "return_code": 124,
                "output": trunc(f"Timed out after {TEST_TIMEOUT}s\n{partial}")}

    out = (r.stdout + r.stderr).strip()
    if r.returncode == 5 and runner == "pytest":
        out = "No tests were collected.\n" + out
    return {
        "runner": runner,
        "passed": r.returncode == 0,
        "return_code": r.returncode,
        "output": trunc(out) if out else "(no output)",
    }


SCHEMAS = [
    tool(
        "run_tests",
        "Run the project's tests (pytest if installed, else unittest). "
        "Optional path to a test file or folder. Returns JSON with "
        "passed, return_code and output.",
        {"path": {"type": "string", "description": "optional test file or folder"}},
        [],
    ),
]