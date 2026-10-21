from . import filesystem, terminal, search, git, testing, analysis
from .filesystem import read_file, write_file, list_dir, edit_file
from .terminal import run_command
from .search import search_code, find_files
from .git import git_status, git_diff, git_log, git_commit
from .testing import run_tests
from .analysis import check_syntax, outline

TOOLS = (
    filesystem.SCHEMAS
    + terminal.SCHEMAS
    + search.SCHEMAS
    + git.SCHEMAS
    + testing.SCHEMAS
    + analysis.SCHEMAS
)

REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
    "edit_file": edit_file,
    "run_command": run_command,
    "search_code": search_code,
    "find_files": find_files,
    "git_status": git_status,
    "git_diff": git_diff,
    "git_log": git_log,
    "git_commit": git_commit,
    "run_tests": run_tests,
    "check_syntax": check_syntax,
    "outline": outline,
}