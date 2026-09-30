import json
from tools import REGISTRY, TOOLS

_SPEC = {t["function"]["name"]: t["function"]["parameters"] for t in TOOLS}


def run_tool(name, args_json):
    if name not in REGISTRY:
        return f"ERROR: unknown tool '{name}'. Available: {', '.join(REGISTRY)}"

    try:
        args = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError as e:
        return f"ERROR: arguments are not valid JSON: {e}"
    if not isinstance(args, dict):
        return "ERROR: arguments must be a JSON object"

    spec = _SPEC[name]
    missing = [a for a in spec.get("required", []) if a not in args]
    if missing:
        return f"ERROR: missing required argument(s): {', '.join(missing)}"
    unexpected = [a for a in args if a not in spec["properties"]]
    if unexpected:
        allowed = ", ".join(spec["properties"])
        return f"ERROR: unexpected argument(s): {', '.join(unexpected)}. Allowed: {allowed}"

    try:
        result = REGISTRY[name](**args)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"

    return result if isinstance(result, str) else json.dumps(result)