import json
import tools

print(json.dumps(tools.TOOLS, indent=1)[:400])

for t in tools.TOOLS:
    name = t["function"]["name"]
    assert hasattr(tools, name), f"No function named {name}"
    assert name in tools.REGISTRY, f"{name} missing from REGISTRY"

# Behaviour checks
print(tools.write_file("tmp_check/t.txt", "hello"))
print(tools.edit_file("tmp_check/t.txt", "hello", "hi"))
assert tools.read_file("tmp_check/t.txt") == "hi"
print(tools.list_dir("tmp_check"))
print(tools.run_command("python -c \"print('ok')\""))
print(tools.run_command("python -c \"while True: pass\"", timeout=2))
try:
    tools.read_file("../secret.txt")
    raise SystemExit("Path guard FAILED")
except ValueError as e:
    print("Path guard OK:", e)

import shutil
shutil.rmtree("tmp_check")
print("All tool checks passed.")
