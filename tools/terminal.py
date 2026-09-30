import subprocess

from .common import WORKSPACE, trunc, tool, S


def run_command(command, timeout=60):
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"Timed out after {timeout}s"}
    return {
        "stdout": trunc(r.stdout),
        "stderr": trunc(r.stderr),
        "return_code": r.returncode,
    }


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
