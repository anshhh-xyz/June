"""core/verifier.py - does deterministic verification using June's own tools."""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class VerifyResult:
    passed: bool
    summary: str
    checks: list = field(default_factory=list)

    @property
    def feedback(self) -> str:
        return "\n".join(self.checks) if self.checks else self.summary


def _changed_py_files(status_text: str) -> list:
    files = set()
    for line in status_text.replace("\\", "/").splitlines():
        for tok in line.split():
            tok = tok.strip("'\"")
            if tok.endswith(".py"):
                files.add(tok)
    return sorted(files)


def _parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def verify(run_tool, force_tests: bool = False) -> VerifyResult:
    """run_tool(name, args_json) -> str (the executor's run_tool)."""
    checks, failed = [], False

    status = run_tool("git_status", "{}")
    changed = _changed_py_files(status) if isinstance(status, str) else []

    # 1. syntax of every changed python file
    for f in changed:
        out = run_tool("check_syntax", json.dumps({"path": f}))
        low = out.lower()
        if "no such file" in low or "not found" in low:
            continue  # deleted or renamed file
        if out.startswith("ERROR") or "syntaxerror" in low:
            failed = True
            checks.append(f"SYNTAX FAIL {f}: {out[:400]}")
        else:
            checks.append(f"syntax ok: {f}")

    # 2. tests: only when code changed (or forced at the very end)
    if changed or force_tests:
        out = run_tool("run_tests", "{}")
        data = _parse_json(out)
        if isinstance(data, dict) and "passed" in data:
            code = data.get("return_code")
            text = str(data.get("output", ""))
            if code == 5 or "no tests ran" in text.lower():
                checks.append("tests: none found (skipped)")
            elif data["passed"]:
                checks.append("tests: PASSED")
            else:
                failed = True
                checks.append(f"TESTS FAILED (exit {code}):\n{text[-1500:]}")
        else:
            low = out.lower()
            if "no tests ran" in low:
                checks.append("tests: none found (skipped)")
            elif out.startswith("ERROR") or " failed" in low or "error" in low:
                failed = True
                checks.append(f"TESTS FAILED:\n{out[-1500:]}")
            else:
                checks.append("tests: PASSED")
    else:
        checks.append("no code changes, tests skipped")

    return VerifyResult(
        passed=not failed,
        summary="verification FAILED" if failed else "verification passed",
        checks=checks,
    )