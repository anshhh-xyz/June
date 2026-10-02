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

# Cleanup
shutil.rmtree("tmp_check")
print("All tool checks passed.")