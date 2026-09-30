import time

import groq
from groq import Groq

from .key_manager import KeyManager, AllKeysUnavailable

DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_AUTO_WAIT = 60      # if all keys cool down for <= this many seconds, just wait
MAX_TRANSIENT = 2       # retries for network / server errors
MAX_TOOL_FLAKES = 2     # retries when the model emits a malformed tool call

_manager = None
_clients = {}


def get_manager():
    global _manager
    if _manager is None:
        _manager = KeyManager()
    return _manager


def _client_for(key):
    if key not in _clients:
        _clients[key] = Groq(api_key=key, max_retries=0)
    return _clients[key]


def _call(key, messages, tools, model):
    kwargs = {"model": model, "messages": messages}
    if tools:
        kwargs.update(tools=tools, tool_choice="auto")
    response = _client_for(key).chat.completions.create(**kwargs)
    return response.choices[0].message


def _retry_after(error, default=60.0):
    try:
        return float(error.response.headers.get("retry-after", default))
    except (AttributeError, TypeError, ValueError):
        return default


def ask_groq(messages, tools=None, model=DEFAULT_MODEL):
    mgr = get_manager()
    transient = 0
    tool_flakes = 0

    while True:
        picked = mgr.get_available_key()
        if picked is None:
            wait = mgr.seconds_until_available()
            if wait is not None and wait <= MAX_AUTO_WAIT:
                print(f"  [all keys rate-limited; waiting {wait:.0f}s]")
                time.sleep(wait + 1)
                continue
            raise AllKeysUnavailable(wait)

        idx, key = picked
        try:
            return _call(key, messages, tools, model)

        except groq.RateLimitError as e:
            wait = _retry_after(e)
            print(f"  [{mgr.label(idx)} rate-limited ({wait:.0f}s); trying next key]")
            mgr.mark_key_failed(idx, cooldown=wait)

        except (groq.AuthenticationError, groq.PermissionDeniedError):
            print(f"  [{mgr.label(idx)} rejected (invalid/revoked); trying next key]")
            mgr.mark_key_failed(idx, permanent=True)

        except (groq.APIConnectionError, groq.InternalServerError):
            transient += 1
            if transient > MAX_TRANSIENT:
                raise
            time.sleep(2 * transient)

        except groq.BadRequestError as e:
            if "tool_use_failed" in str(e) and tool_flakes < MAX_TOOL_FLAKES:
                tool_flakes += 1
                continue
            raise