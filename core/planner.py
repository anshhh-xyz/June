"""The planner makes a tool-less LLM call and parses the JSON that comes back. 
Models often wrap JSON in markdown fences or add chatter, so the parser tolerates that."""

from __future__ import annotations

import json
import re

from core.state import Step
from models.prompts import PLANNER_SYSTEM


def _extract_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    for opener, closer in (("{", "}"), ("[", "]")):
        i, j = text.find(opener), text.rfind(closer)
        if i != -1 and j > i:
            try:
                return json.loads(text[i : j + 1])
            except json.JSONDecodeError:
                continue
    return None


def parse_plan(text: str, max_steps: int = 8) -> list:
    data = _extract_json(text or "")
    if isinstance(data, dict):
        data = data.get("steps")
    if not isinstance(data, list):
        return []
    steps = []
    for item in data:
        if isinstance(item, str):
            title, detail = item.strip(), ""
        elif isinstance(item, dict):
            title = str(item.get("title") or item.get("step") or "").strip()
            detail = str(item.get("detail") or item.get("description") or "").strip()
        else:
            continue
        if title:
            steps.append(Step(id=len(steps) + 1, title=title, detail=detail))
        if len(steps) >= max_steps:
            break
    return steps


def make_plan(goal, llm, context="", failure="", done_text="", max_steps=8) -> list:
    """llm(system, user, role) -> str. Falls back to a single step if parsing fails."""
    user = f"GOAL:\n{goal}\n"
    if context:
        user += f"\nPROJECT SNAPSHOT:\n{context}\n"
    if done_text:
        user += f"\nALREADY DONE:\n{done_text}\n"
    if failure:
        user += f"\nA PREVIOUS PLAN FAILED HERE. Plan only the REMAINING work and avoid the same failure:\n{failure}\n"
    raw = llm(PLANNER_SYSTEM, user, "planner")
    steps = parse_plan(raw, max_steps)
    return steps or [Step(id=1, title="Complete the task", detail=goal)]