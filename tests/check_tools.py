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


# Cleanup
shutil.rmtree("tmp_check")
print("All tool checks passed.")