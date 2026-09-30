from pathlib import Path

WORKSPACE = Path(".").resolve()


def safe(path):
    p = (WORKSPACE / path).resolve()
    if not p.is_relative_to(WORKSPACE):
        raise ValueError(f"Path outside workspace: {path}")
    return p


def trunc(text, limit=4000):
    if len(text) <= limit:
        return text
    return f"[...truncated {len(text) - limit} chars...]\n" + text[-limit:]


def tool(name, desc, props, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        },
    }


S = {"type": "string"}
