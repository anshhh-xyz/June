import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class NoKeysConfigured(RuntimeError):
    pass


class AllKeysUnavailable(RuntimeError):
    def __init__(self, wait):
        self.wait = wait
        if wait is None:
            msg = "All Groq API keys are invalid or revoked."
        else:
            msg = f"All Groq API keys are rate-limited. Soonest retry in ~{wait:.0f}s."
        super().__init__(msg)


def load_keys_from_env():
    names = ["GROQ_API_KEY"] + [f"GROQ_API_KEY_{i}" for i in range(1, 11)]
    keys = []
    for name in names:
        value = os.environ.get(name, "").strip()
        if value and value not in keys:
            keys.append(value)
    return keys


class KeyManager:
    def __init__(self, keys=None):
        self.keys = list(keys) if keys is not None else load_keys_from_env()
        if not self.keys:
            raise NoKeysConfigured("No Groq keys found. Set GROQ_API_KEY_1 in .env")
        self._until = {}  
        self._current = 0   

    def label(self, index):
        return f"key #{index + 1}"   

    def get_available_key(self):
        now = time.time()
        n = len(self.keys)
        for offset in range(n):
            i = (self._current + offset) % n
            if self._until.get(i, 0) <= now:
                self._current = i
                return i, self.keys[i]
        return None

    def mark_key_failed(self, index, cooldown=60.0, permanent=False):
        self._until[index] = float("inf") if permanent else time.time() + cooldown

    def mark_key_available(self, index):
        self._until.pop(index, None)

    def seconds_until_available(self):
        times = [self._until.get(i, 0) for i in range(len(self.keys))]
        soonest = min(times)
        if soonest == float("inf"):
            return None
        return max(0.0, soonest - time.time())