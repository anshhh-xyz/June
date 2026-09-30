from . import filesystem, terminal
from .filesystem import read_file, write_file, list_dir, edit_file
from .terminal import run_command

TOOLS = filesystem.SCHEMAS + terminal.SCHEMAS

REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
    "edit_file": edit_file,
    "run_command": run_command,
}
