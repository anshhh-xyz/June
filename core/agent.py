from tools import TOOLS
from models.groq_client import ask_groq
from .executor import run_tool

MAX_STEPS = 15


def _short(text, n=100):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n] + "..."


def run_agent(messages, tools=None, max_steps=MAX_STEPS, ask=ask_groq, verbose=True):
    tools = TOOLS if tools is None else tools

    for _ in range(max_steps):
        msg = ask(messages, tools)

        if not msg.tool_calls:
            answer = msg.content or ""
            messages.append({"role": "assistant", "content": answer})
            return answer

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.function.name,
                                 "arguments": c.function.arguments},
                }
                for c in msg.tool_calls
            ],
        })

        for c in msg.tool_calls:
            name, args = c.function.name, c.function.arguments
            if verbose:
                print(f"  -> {name}({_short(args)})")
            result = run_tool(name, args)
            if verbose:
                status = "ERR" if result.startswith("ERROR") else "ok"
                print(f"     [{status}] {_short(result, 80)}")
            messages.append({"role": "tool", "tool_call_id": c.id, "content": result})

    note = f"Stopped after {max_steps} steps without finishing. Try a narrower request."
    messages.append({"role": "assistant", "content": note})
    return note