import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import shutil
import tools

print(json.dumps(tools.TOOLS, indent=1)[:400])

for t in tools.TOOLS:
    name = t["function"]["name"]
    assert hasattr(tools, name), f"No function named {name}"
    assert name in tools.REGISTRY, f"{name} missing from REGISTRY"

# Behaviour checks
print(tools.write_file("tmp_check/t.txt", "hello"))
print(tools.edit_file("tmp_check/t.txt", "hello", "hi"))
assert "1: hi" in tools.read_file("tmp_check/t.txt")
print(tools.list_dir("tmp_check"))
print(tools.run_command("python -c \"print('ok')\""))
print(tools.run_command("python -c \"while True: pass\"", timeout=2))
try:
    tools.read_file("../secret.txt")
    raise SystemExit("Path guard FAILED")
except ValueError as e:
    print("Path guard OK:", e)

# --- read_file range checks ---
tools.write_file("tmp_check/ten.txt", "\n".join(f"line {i}" for i in range(1, 11)))

full = tools.read_file("tmp_check/ten.txt")
assert "1-10 of 10" in full and "5: line 5" in full

part = tools.read_file("tmp_check/ten.txt", start=3, end=5)
assert "3: line 3" in part and "5: line 5" in part
assert "6: line 6" not in part and "2: line 2" not in part

assert "1-10 of 10" in tools.read_file("tmp_check/ten.txt", end=999)      # clamp
assert "10: line 10" in tools.read_file("tmp_check/ten.txt", start=10)    # only last line
assert tools.read_file("tmp_check/ten.txt", start=999).startswith("ERROR")
assert tools.read_file("tmp_check/ten.txt", start=5, end=2).startswith("ERROR")
assert tools.read_file("tmp_check/ten.txt", start=0).startswith("ERROR")
assert tools.read_file("tmp_check/ten.txt", start="abc").startswith("ERROR")
print("read_file range checks OK")

# --- search checks ---
from pathlib import Path
from tools import search

tools.write_file("tmp_check/s/a.py", "def hello():\n    return 1\n")
tools.write_file("tmp_check/s/sub/b.py", "x = 'hello world'\n")
tools.write_file("tmp_check/s/__pycache__/c.py", "hello hidden\n")
Path("tmp_check/s/bin.dat").write_bytes(b"hello\x00\x01\x02")

r = search.search_code("hello", "tmp_check/s")
assert "a.py:1:" in r and "b.py:1:" in r
assert "__pycache__" not in r, "SKIP folder was searched"
assert "bin.dat" not in r, "binary file was searched"

assert search.search_code("zzzznotfound", "tmp_check/s") == "No matches."
assert search.search_code("(unclosed", "tmp_check/s").startswith("ERROR")
assert search.search_code("hello", "tmp_check/nope").startswith("ERROR")

tools.write_file("tmp_check/s/many.txt", "\n".join("match" for _ in range(80)))
assert "truncated" in search.search_code("match", "tmp_check/s")

f = search.find_files("*.py")
assert "tmp_check/s/a.py" in f and "__pycache__" not in f

try:
    search.search_code("x", "../")
    raise SystemExit("search path guard FAILED")
except ValueError:
    pass
print("search checks OK")


# --- git checks ---
import tempfile
from tools import git

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as repo:
    git.WORKDIR = repo
    try:
        assert git._git("init")[0] == 0
        git._git("config", "user.name", "Test")
        git._git("config", "user.email", "test@example.com")

        (Path(repo) / "a.txt").write_text("one\n")
        assert "a.txt" in git.git_status()

        assert git.git_commit("").startswith("ERROR")
        first = git.git_commit("first commit")
        assert not first.startswith("ERROR") and "first commit" in first

        again = git.git_commit("nothing new")
        assert not again.startswith("ERROR") and "nothing to commit" in again.lower()

        (Path(repo) / "a.txt").write_text("two\n")
        d = git.git_diff()
        assert "-one" in d and "+two" in d
        assert "first commit" in git.git_log()
        assert not git.git_log(999).startswith("ERROR")   # clamped, not an error
    finally:
        git.WORKDIR = None

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as notrepo:
    git.WORKDIR = notrepo
    try:
        assert git.git_status().startswith("ERROR")        # readable error, no crash
    finally:
        git.WORKDIR = None

try:
    git.git_diff("../")
    raise SystemExit("git_diff path guard FAILED")
except ValueError:
    pass
print("git checks OK")

# --- analysis checks ---
tools.write_file("tmp_check/a/good.py",
                 "class A:\n    def m(self, x):\n        return x\n\ndef f(a, b=1):\n    return a\n")
tools.write_file("tmp_check/a/bad.py", "def broken(:\n    pass\n")

assert tools.check_syntax("tmp_check/a/good.py").startswith("OK")
bad = tools.check_syntax("tmp_check/a/bad.py")
assert bad.startswith("SYNTAX ERROR") and "line 1" in bad
assert tools.check_syntax("tmp_check/a/nope.py").startswith("ERROR")

o = tools.outline("tmp_check/a/good.py")
assert "class A" in o and "def m(self, x)" in o and "def f(a, b=1)" in o
assert tools.outline("tmp_check/a/bad.py").startswith("ERROR")
print("analysis checks OK")

# --- run_tests checks ---
tools.write_file("tmp_check/rt/calculator.py", "def add(a, b):\n    return a - b\n")
tools.write_file(
    "tmp_check/rt/test_calculator.py",
    "import unittest\nfrom calculator import add\n\n"
    "class T(unittest.TestCase):\n"
    "    def test_add(self):\n"
    "        self.assertEqual(add(2, 3), 5)\n",
)
r = tools.run_tests("tmp_check/rt")
assert r["passed"] is False, r            # planted bug must be caught

tools.edit_file("tmp_check/rt/calculator.py", "a - b", "a + b")
r = tools.run_tests("tmp_check/rt")
assert r["passed"] is True, r             # fixed

assert tools.run_tests("tmp_check/nope")["passed"] is False
try:
    tools.run_tests("../")
    raise SystemExit("run_tests path guard FAILED")
except ValueError:
    pass
print("run_tests checks OK")


# Cleanup
shutil.rmtree("tmp_check")
print("All tool checks passed.")