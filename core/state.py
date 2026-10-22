from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATE_FILE = Path(".june") / "state.json"

PENDING, RUNNING, DONE, FAILED = "pending", "running", "done", "failed"

@dataclass 
class Step:
    id:str
    title:str
    detail:str
    status:str=PENDING
    attempt:int=0
    result:str=""
    error:str=""

@dataclass
class TaskState:
    goal: str
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    status: str = "planning"  # planning | executing | done | failed
    steps: list = field(default_factory=list)
    replans: int = 0
    errors: list = field(default_factory=list)
    updated: float = field(default_factory=time.time)

    def next_step(self):
        for s in self.steps:
            if s.status in (PENDING, RUNNING):
                return s
        return None
    
    def done_text(self, limit: int = 300) -> str:
        lines = [
            f"- Step {s.id} ({s.title}): {s.result[:limit]}"
            for s in self.steps
            if s.status == DONE
        ]
        return "\n".join(lines) if lines else "(nothing yet)"

    def plan_text(self) -> str:
        mark = {PENDING: "[ ]", RUNNING: "[>]", DONE: "[x]", FAILED: "[!]"}
        return "\n".join(f"{mark.get(s.status, '[ ]')} {s.id}. {s.title}" for s in self.steps)

    def save(self, path: Path = STATE_FILE) -> None:
        self.updated = time.time()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = STATE_FILE):
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["steps"] = [Step(**s) for s in data.get("steps", [])]
            return cls(**data)
        except Exception:
            return None

    