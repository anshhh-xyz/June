import os
import signal
import subprocess
import sys

from .common import WORKSPACE, trunc, tool, S

def _kill_tree(p):
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
    else:
        os.killpg(p.pid, signal.SIGKILL)

def run_command(command, timeout=60):
    p = subprocess.Popen(
        command, shell=True, cwd=WORKSPACE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace",
        start_new_session=(sys.platform != "win32"),
    )
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(p)
        p.communicate()          # collect leftovers so nothing hangs
        return {"error": f"Timed out after {timeout}s"}
    return {"stdout": trunc(out), "stderr": trunc(err), "return_code": p.returncode}

SCHEMAS = [
    tool(
        "run_command",
        "Run a shell command in the workspace. Returns stdout, stderr "
        "and return_code. Use it to run code, tests and installs. "
        "60s timeout; no interactive input.",
        {"command": S},
        ["command"],
    ),
]
