# June — Development Roadmap & Progress Tracker

June is a self-built coding agent: Groq models for reasoning, Python tools for
action, and (later) RAG for memory. This file tracks the build **phase by phase**.

_Last updated: 2026-10-01_

**Legend:** `[x]` done · `[ ]` to do · ⚠️ known issue · ❓ needs confirmation

---

## Overview

| Phase | Goal | Status |
|---|---|---|
| 0. Foundation | Folders, `.env`, `.gitignore`, Git | Mostly done |
| 1. Minimal agent | User → Groq → tool → result → Groq → answer | Code written, 1 bug to fix, real-run tests unconfirmed |
| 2. Coding agent | Modify a small repo and verify the changes | Started (files created, still empty) |
| 3. Planning | Planner, verifier, state, router, agent roles | Not started |
| 4. Memory | Episodic + semantic memory, vector store (RAG) | Not started |
| 5. Safety | Permissions, approval, sandbox | Not started |
| 6. Advanced | Web search, parallel tools, model routing, MCP | Not started |
| 7. User interface | FastAPI backend, web/desktop UI, diff viewer | Not started |

**➡️ Current position: end of Phase 1 / start of Phase 2.**

Rule of the roadmap: do NOT build every module at once. Finish a phase, pass its
test, commit, then move on.

---

## Target project layout

```
June/
├── main.py                 entry point only (input/output loop)
├── user_input.py
├── check_tools.py          offline tool tests (project root!)
├── requirements.txt        groq, python-dotenv
├── .env                    API keys (never committed)
├── .env.example            template with empty values
├── .gitignore
├── core/
│   ├── agent.py            the agent loop
│   └── executor.py         validates + runs tool calls
├── models/
│   ├── groq_client.py      the ONLY file that talks to Groq
│   ├── key_manager.py      multi-key loading + failover state
│   └── prompts.py          system prompts
└── tools/
    ├── common.py           shared helpers (safe path guard, trunc, schema builder)
    ├── filesystem.py       list_dir, read_file, write_file, edit_file
    ├── terminal.py         run_command
    ├── search.py           (Phase 2) search_code, find_files
    ├── git.py              (Phase 2) status, diff, log, commit
    ├── testing.py          (Phase 2) run_tests
    └── analysis.py         (Phase 2) check_syntax, outline
```

Design rules (from the architecture doc):
- The LLM **chooses** tools and arguments; Python **validates and executes**.
- Tools live in a registry (no `if/elif` chains); each tool has a schema.
- Tools return structured/clear results; errors come back as text so the model can recover.
- `main.py` is only the entry point; the loop lives in `core/`; API calls live in `models/`.

---

## Phase 0 — Foundation

- [x] Project folders and Python files created
- [x] `.gitignore` (`.env`, `__pycache__/`, venvs, temp test files)
- [ ] `git init` and first commit of June itself
- [ ] `requirements.txt` (`groq`, `python-dotenv`)
- [ ] `.env.example` committed; real `.env` created locally with `GROQ_API_KEY_1` … `_5`
- [ ] `pip install -r requirements.txt`

---

## Phase 1 — Minimal agent

**Goal:** `User → Groq → tool → result → Groq → answer`

### 1.1 Tools
- [x] `tools/common.py`: `safe()` path guard, `trunc()`, `tool()` schema builder
- [x] `tools/filesystem.py`: `list_dir`, `read_file`, `write_file`, `edit_file` (+ schemas)
- [x] `tools/terminal.py`: `run_command` (60s timeout, no stdin, UTF-8, truncated output)
- [x] `tools/__init__.py`: exposes `TOOLS` and `REGISTRY`
- [ ] ⚠️ Move `check_tools.py` from `tools/` to the project root and run it

### 1.2 Model layer
- [x] `models/key_manager.py`: loads keys from env, per-key cooldowns, sticky current key
- [x] Groq client with failover (429 → cooldown, 401/403 → dead, 5xx → retry, `tool_use_failed` → retry)
- [ ] ⚠️ **Rename `models/groq_clients.py` → `models/groq_client.py`** (`core/agent.py` imports the name without the "s"; right now `python main.py` crashes with `ModuleNotFoundError`)
- [x] `models/prompts.py`: Phase 1 system prompt

### 1.3 Core
- [x] `core/executor.py`: `run_tool(name, args_json)`: validates, runs, returns `ERROR:` strings instead of crashing
- [x] `core/agent.py`: loop with 15-step cap and progress printing
- [x] `main.py`: slim input loop, history rollback on failed turns

### 1.4 Phase 1 exam (run in a throwaway folder!)
- [ ] ❓ Test 1: "List the files here and tell me what this project does."
- [ ] ❓ Test 2: "Create `hello.py` that prints Fibonacci numbers up to 100, then run it."
- [ ] ❓ Test 3: "Change it to go up to 1000 and verify."
- [ ] ❓ Test 4: plant a bug in a script → June reads the traceback, edits, re-runs, confirms the fix

**Phase 1 is DONE when Test 4 passes with no help from you.**

---

## Phase 2 — Coding agent

**Goal:** June can modify a small repository and verify its changes.

Order of work:

### 2.1 Small upgrades to existing code
- [ ] Move `SKIP` into `tools/common.py` and import it in `filesystem.py`
- [ ] Upgrade `read_file` with optional `start` / `end` line arguments (return numbered lines) — biggest token saver

### 2.2 `tools/search.py` — code search
- [ ] `search_code(pattern, path=".")`: regex over files, skip `SKIP` folders and binaries, return `path:line: text`, cap ~50 results
- [ ] `find_files(pattern)`: glob search, capped
- [ ] Schemas + `SCHEMAS` list

### 2.3 `tools/git.py` — Git
- [ ] `_git(*args)` helper (no `shell=True`, timeout, `trunc` output)
- [ ] `git_status`, `git_diff`, `git_log`, `git_commit(message)`
- [ ] Deliberately NO push / reset --hard / clean (wait for Phase 5 approvals)

### 2.4 `tools/testing.py` — test runner
- [ ] `run_tests(path=None)`: pytest if installed, else `unittest discover`; ~120s timeout
- [ ] Return structured result: `{"passed": bool, "return_code": int, "output": "..."}`

### 2.5 `tools/analysis.py` — code analysis
- [ ] `check_syntax(path)` using `ast.parse`
- [ ] `outline(path)`: classes/functions with line numbers (cheap file map)

### 2.6 Wire it together
- [ ] Register all new modules in `tools/__init__.py` (`TOOLS` and `REGISTRY`)
- [ ] Extend `check_tools.py` (names resolve, search works, syntax check passes/fails correctly)
- [ ] Update `AGENT_PROMPT` with the verification workflow: search/outline → read only needed lines → `edit_file` → `check_syntax` → `run_tests` → `git_diff` → `git_commit` only when tests pass

### 2.7 Phase 2 exam
Scratch repo: `git init`, a small `calculator.py` with a planted bug, a `test_calculator.py` with a failing test, committed.

Prompt: _"The tests are failing. Find the bug, fix it, verify, and commit."_

- [ ] June runs the tests and sees the failure
- [ ] June locates the function with search/outline
- [ ] June fixes it with `edit_file`
- [ ] Tests pass on re-run
- [ ] June reviews the diff and commits
- [ ] Stretch: "Add a `power(a, b)` function with tests"

---

## Phase 3 — Planning

**Goal:** June performs multi-step coding tasks autonomously.

Logical agent roles (separate model calls coordinated by `core/agent.py`, not separate programs):
Planner · Coder · Researcher · Verifier · Summarizer

- [ ] Reuse the Phase 1 loop as the **Coder** (it already takes `tools` and `ask` as parameters)
- [ ] `planner.py`: turns a request into ordered steps
- [ ] `verifier.py`: checks results (uses `run_tests`' `passed` field, `git_diff`)
- [ ] `state.py`: tracks task/step progress
- [ ] `router.py`: decides which role/model handles what
- [ ] Split executor responsibilities if needed

---

## Phase 4 — Memory (RAG)

**Goal:** June remembers useful project context across tasks.

- [ ] Episodic memory (what happened in past tasks)
- [ ] Semantic memory (facts about the project)
- [ ] Vector store
- [ ] Retriever
- [ ] Summarizer role to compress long conversation history (history currently grows every turn)

Note: for code lookup, plain text search (Phase 2) usually beats embeddings. Use the vector store for past decisions and project notes.

---

## Phase 5 — Safety

**Goal:** June operates autonomously without unrestricted destructive access.

- [ ] Permissions (read-only vs. mutating tools)
- [ ] Approval flow for risky actions (delete, push, reset, installs)
- [ ] Sandbox for `run_command` (today `cwd` is NOT a sandbox)
- [ ] Re-add guarded destructive Git operations behind approval

Until this phase is done: run June only in throwaway or Git-tracked folders.

---

## Phase 6 — Advanced capabilities

- [ ] Web search
- [ ] Parallel tool calls
- [ ] Model routing (cheap/fast model for simple steps; big model for hard ones; limits are per model)
- [ ] MCP / external tools
- [ ] Process management
- [ ] Long-running tasks
- [ ] Optional second provider behind the same `models/` interface (real failover)

---

## Phase 7 — User interface

- [ ] FastAPI backend
- [ ] Web/desktop UI
- [ ] Streaming responses
- [ ] Task status view
- [ ] Approval UI
- [ ] Diff viewer

---

## Notes & decisions log

- Native tool calling is used (`tools=` + `tool_choice="auto"`); strict JSON-schema output is not combined with tools.
- Multiple Groq keys: loaded from `GROQ_API_KEY_1..N`; sticky until a key fails. Keys are never logged. Groq rate limits are generally scoped per organization/account and per model, and providers' terms may restrict creating accounts to bypass limits — check Groq's terms; model routing and context trimming are the safe ways to stretch limits.
- Keep tool descriptions short: every schema is sent with every request.
- Truncate tool output (`trunc`) to protect the token budget.
- Workflow habit: test each step with `check_tools.py` before moving on; commit after each passing step.

---

## Immediate next actions

1. Rename `models/groq_clients.py` → `models/groq_client.py`.
2. Move `check_tools.py` to the project root; run it.
3. Create `.env`, run `python main.py` in a throwaway folder, and pass Tests 1–4.
4. Commit. Then start Phase 2, step 2.1.
