# June --- Autonomous Coding Agent

## 1. Vision

**June** is a modular, agentic coding assistant designed to provide the
capabilities of a modern IDE coding agent: understand a project, inspect
and modify code, execute commands, run tests, research information, use
external tools, remember project context, recover from failures, and ask
for approval before risky actions.

June should not be a simple chatbot that generates code. Its core loop
is:

``` text
User Request
     ↓
Understand
     ↓
Retrieve relevant context / memory
     ↓
Plan
     ↓
Select tools
     ↓
Execute
     ↓
Observe results
     ↓
Verify
     ↓
Retry / Re-plan if necessary
     ↓
Final response
```

The architecture should remain modular so that models, tools, memory
systems, and interfaces can be replaced independently.

------------------------------------------------------------------------

# 2. Core Design Principles

### Agent-first

June should reason about a task and take actions rather than only return
text.

### Tool-driven

File operations, terminal commands, Git, testing, search, and other
actions should be performed through explicit tools.

### Project-aware

June should understand the repository it is working in and retrieve only
relevant context instead of dumping an entire codebase into the prompt.

### Verification-first

June should verify changes using tests, linting, type checking, builds,
or other appropriate checks.

### Human-controlled

Risky operations should require explicit approval.

### Model-agnostic

Groq should initially provide the model backend, but June should be able
to support multiple models and route tasks to appropriate models later.

### Persistent memory

June should remember useful project facts, previous tasks, decisions,
and relevant history without blindly storing everything.

------------------------------------------------------------------------

# 3. Repository Structure

``` text
june/
│
├── core/
│   ├── agent.py
│   ├── planner.py
│   ├── router.py
│   ├── executor.py
│   ├── verifier.py
│   └── state.py
│
├── models/
│   ├── groq_client.py
│   ├── model_router.py
│   └── prompts.py
│
├── tools/
│   ├── filesystem.py
│   ├── terminal.py
│   ├── git.py
│   ├── code_search.py
│   ├── code_analysis.py
│   ├── test_runner.py
│   ├── web_search.py
│   └── process.py
│
├── memory/
│   ├── episodic.py
│   ├── semantic.py
│   ├── vector_store.py
│   └── retriever.py
│
├── safety/
│   ├── permissions.py
│   ├── sandbox.py
│   └── approval.py
│
├── api/
│   └── server.py
│
└── main.py
```

------------------------------------------------------------------------

# 4. Core

## `core/agent.py`

The main agent loop.

Responsibilities:

-   receive a task
-   maintain conversation/task state
-   call the planner
-   request tool calls
-   send tool results back to the model
-   determine when the task is complete
-   trigger verification
-   retry or re-plan after failures
-   produce the final response

Conceptually:

``` text
while task_not_finished:

    understand current state
    retrieve context
    plan
    choose action
    execute action
    observe result
    verify

    if failed:
        re-plan

return final result
```

------------------------------------------------------------------------

## `core/planner.py`

Converts a high-level request into an actionable plan.

Example:

``` text
User:
"Add authentication to this FastAPI application."

Plan:

1. Inspect project structure
2. Find current API entry point
3. Inspect dependency configuration
4. Inspect existing user/authentication code
5. Decide implementation
6. Modify required files
7. Install/update dependencies if necessary
8. Run tests
9. Fix failures
10. Run final verification
```

The planner should not directly modify files.

------------------------------------------------------------------------

## `core/router.py`

Determines what should happen next.

It can select:

-   a tool
-   a model
-   a planner
-   a verifier
-   a memory source
-   multiple tools in parallel

Example:

``` text
Need repository information
        ↓
code_search / filesystem

Need to execute code
        ↓
terminal

Need Git information
        ↓
git

Need external information
        ↓
web_search
```

------------------------------------------------------------------------

## `core/executor.py`

Responsible for executing approved tool calls.

Responsibilities:

-   validate tool arguments
-   check permissions
-   execute tools
-   capture output
-   capture errors
-   return structured results
-   prevent malformed tool calls from crashing the agent

------------------------------------------------------------------------

## `core/verifier.py`

Determines whether June actually succeeded.

Possible verification:

-   unit tests
-   integration tests
-   linting
-   formatting
-   type checking
-   compilation
-   build
-   application startup
-   command exit codes
-   Git diff inspection

June should prefer:

``` text
"I changed it and verified it."
```

over:

``` text
"I think I changed it correctly."
```

------------------------------------------------------------------------

## `core/state.py`

Stores the current task state.

Example:

``` json
{
  "task_id": "...",
  "goal": "...",
  "status": "executing",
  "current_step": 3,
  "completed_steps": [],
  "pending_steps": [],
  "tool_results": [],
  "errors": [],
  "files_changed": []
}
```

This allows June to recover from failures and maintain long-running
tasks.

------------------------------------------------------------------------

# 5. Models

## `models/groq_client.py`

The only module that should directly communicate with Groq.

Responsibilities:

-   API authentication
-   model requests
-   structured outputs
-   tool calling
-   streaming
-   retries
-   API error handling
-   token/usage tracking

The rest of June should not need to know the details of the Groq API.

------------------------------------------------------------------------

## `models/model_router.py`

Chooses the appropriate model for a task.

Examples:

``` text
Simple classification      → fast/cheap model
Code generation            → coding-capable model
Complex debugging          → stronger reasoning model
Summarization              → small/fast model
Verification               → reasoning model
```

Model selection should be configurable rather than hard-coded throughout
the project.

------------------------------------------------------------------------

## `models/prompts.py`

Central location for system prompts and reusable prompt templates.

Examples:

-   agent prompt
-   planner prompt
-   tool-selection prompt
-   verifier prompt
-   summarizer prompt
-   memory extraction prompt

------------------------------------------------------------------------

# 6. Tools

Tools are June's ability to interact with the real environment.

## `tools/filesystem.py`

Basic file operations:

-   list directory
-   read file
-   create file
-   write file
-   edit file
-   delete file
-   move/rename file
-   inspect file metadata

June should support precise edits rather than unnecessarily rewriting
entire files.

------------------------------------------------------------------------

## `tools/terminal.py`

Execute commands.

Examples:

``` text
python
pip
npm
node
git
pytest
cargo
javac
docker
```

Capabilities:

-   command execution
-   stdout/stderr capture
-   exit codes
-   timeouts
-   working-directory control
-   environment handling

Dangerous commands should pass through the safety layer.

------------------------------------------------------------------------

## `tools/git.py`

Git integration.

Capabilities:

-   status
-   diff
-   log
-   branch information
-   create branch
-   checkout
-   commit
-   stash
-   revert
-   compare changes
-   inspect changed files

Potentially later:

-   GitHub pull requests
-   issues
-   comments
-   repository metadata

------------------------------------------------------------------------

## `tools/code_search.py`

Repository-aware search.

Capabilities:

-   filename search
-   text search
-   regex search
-   symbol search
-   function/class search
-   import/reference search

Prefer fast repository tools such as ripgrep where appropriate.

------------------------------------------------------------------------

## `tools/code_analysis.py`

Understand code structure.

Potential capabilities:

-   AST parsing
-   function extraction
-   class extraction
-   dependency analysis
-   import graph
-   call relationships
-   language detection
-   project structure detection

This becomes increasingly important for large repositories.

------------------------------------------------------------------------

## `tools/test_runner.py`

Run and interpret project verification.

Examples:

``` text
pytest
npm test
npm run build
cargo test
mvn test
gradle test
```

It should return structured results such as:

``` json
{
  "success": false,
  "command": "pytest",
  "exit_code": 1,
  "stdout": "...",
  "stderr": "...",
  "failed_tests": ["test_auth"]
}
```

------------------------------------------------------------------------

## `tools/web_search.py`

External research.

Use cases:

-   documentation
-   API references
-   package information
-   debugging unfamiliar errors
-   current technical information
-   research required by a task

Search results should be returned as structured context rather than
blindly inserted into prompts.

------------------------------------------------------------------------

## `tools/process.py`

Manage running applications and processes.

Potential capabilities:

-   list processes
-   start process
-   stop process
-   inspect process output
-   check whether a service is running
-   monitor development servers

This should be heavily permission-controlled.

------------------------------------------------------------------------

# 7. Memory

Memory should be divided into different types rather than treating
everything as generic RAG.

## `memory/episodic.py`

Stores previous interactions and completed tasks.

Example:

``` text
Task:
Fix authentication bug.

Result:
Changed auth/middleware.py and passed 42 tests.
```

Useful for continuing unfinished work or understanding what June
previously did.

------------------------------------------------------------------------

## `memory/semantic.py`

Stores durable project knowledge.

Examples:

``` text
Project uses FastAPI.
Database is PostgreSQL.
Tests use pytest.
Deployment uses Docker.
User prefers modular architecture.
```

This should contain useful facts rather than raw conversation history.

------------------------------------------------------------------------

## `memory/vector_store.py`

Handles embeddings and vector storage.

Potential implementation:

``` text
Embedding model
      ↓
Vector database
      ↓
Semantic retrieval
```

The vector database can initially be something lightweight and local,
then be replaced later.

------------------------------------------------------------------------

## `memory/retriever.py`

Responsible for deciding what memory/context is relevant to the current
task.

Retrieval sources can include:

-   project documentation
-   source code
-   previous tasks
-   project facts
-   Git history
-   user instructions
-   indexed documentation

June should retrieve relevant context instead of stuffing everything
into the prompt.

------------------------------------------------------------------------

# 8. Safety

## `safety/permissions.py`

Controls which actions June is allowed to perform.

Example permission levels:

``` text
READ
    ↓
automatic

WRITE
    ↓
configurable

RUN COMMAND
    ↓
configurable

DELETE / destructive Git
    ↓
approval required

SYSTEM / credential / destructive operations
    ↓
mandatory approval
```

------------------------------------------------------------------------

## `safety/sandbox.py`

Provides an isolated environment for risky operations.

Potential implementations:

-   temporary directories
-   Git worktrees
-   Docker containers
-   restricted execution environments

The goal is to allow June to experiment without unnecessarily damaging
the user's main project.

------------------------------------------------------------------------

## `safety/approval.py`

Handles human-in-the-loop approval.

June should be able to say:

``` text
I need to run:

pip install <package>

Approve? [y/N]
```

or:

``` text
I am about to delete 3 files.

Approve? [y/N]
```

Approval rules should be configurable.

------------------------------------------------------------------------

# 9. API

## `api/server.py`

Provides a programmatic interface to June.

Potential stack:

``` text
FastAPI
    ↓
June Agent
```

The API can later support:

-   chat requests
-   streaming responses
-   task creation
-   task status
-   tool approval
-   cancellation
-   project selection
-   memory operations

This allows a separate web/desktop UI to communicate with June.

------------------------------------------------------------------------

# 10. Main Entry Point

## `main.py`

`main.py` should stay thin.

It should:

1.  initialize June
2.  receive user input
3.  pass the request to the agent
4.  display responses
5.  handle basic application-level errors

It should **not** contain:

-   tool implementations
-   Groq API logic
-   complex planning
-   memory implementation
-   permission logic

Those belong in their respective modules.

------------------------------------------------------------------------

# 11. Agent Tool-Calling Loop

The fundamental June loop should eventually look like:

``` text
                 USER
                   ↓
             Agent receives task
                   ↓
             Retrieve context
                   ↓
                Planner
                   ↓
              Model decides
                   ↓
             Tool call JSON
                   ↓
              Permission check
                   ↓
              Tool executor
                   ↓
              Tool result
                   ↓
              Model observes
                   ↓
             ┌─────┴─────┐
             │           │
           failed       success
             │           │
             ↓           ↓
          re-plan      verify
             │           │
             └─────┬─────┘
                   ↓
              Final answer
```

June should be capable of making multiple tool calls for a single user
request.

------------------------------------------------------------------------

# 12. Example: "Fix the bug"

User:

``` text
Fix the authentication bug in my project.
```

June should be able to do:

``` text
1. Inspect repository
2. Search for authentication code
3. Inspect relevant files
4. Search Git history if useful
5. Identify likely cause
6. Form a plan
7. Ask approval if required
8. Modify files
9. Run tests
10. Observe failure if tests fail
11. Diagnose
12. Modify again
13. Re-run tests
14. Inspect final diff
15. Report what changed
```

The important part is that June should **continue working after a failed
attempt** instead of immediately giving up.

------------------------------------------------------------------------

# 13. Example: "Build me a website"

June should be capable of:

``` text
Understand requirements
        ↓
Inspect existing project
        ↓
Choose/understand stack
        ↓
Plan files/components
        ↓
Create files
        ↓
Install required dependencies
        ↓
Run development server
        ↓
Inspect build/runtime errors
        ↓
Fix errors
        ↓
Run tests/build
        ↓
Review changes
        ↓
Report result
```

For visual/UI tasks, a future UI layer can provide screenshots or
browser feedback to the agent.

------------------------------------------------------------------------

# 14. Project Understanding

Before making significant changes, June should be able to understand a
project.

Potential discovery:

``` text
README
package files
requirements
pyproject.toml
package.json
Dockerfile
configuration
source structure
tests
Git state
```

Then create a compact project representation:

``` json
{
  "language": "Python",
  "framework": "FastAPI",
  "package_manager": "pip",
  "test_framework": "pytest",
  "entry_points": ["app/main.py"],
  "database": "PostgreSQL"
}
```

This can become part of project memory.

------------------------------------------------------------------------

# 15. Long-Running Tasks

June should eventually support tasks that take multiple iterations.

Example:

``` text
Task created
   ↓
Planning
   ↓
Executing
   ↓
Waiting for approval
   ↓
Executing
   ↓
Testing
   ↓
Failed
   ↓
Retrying
   ↓
Completed
```

`state.py` should make this possible.

------------------------------------------------------------------------

# 16. Parallel Tool Execution

When actions are independent, June should eventually execute them
concurrently.

Example:

``` text
Inspect:
├── package.json
├── README.md
├── src/
└── tests/
```

instead of:

``` text
package.json → wait
README → wait
src → wait
tests → wait
```

Parallel execution should only be used when actions do not depend on
each other.

------------------------------------------------------------------------

# 17. Model Routing

June should eventually separate tasks by difficulty.

``` text
                 User task
                     ↓
                Model Router
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
    Simple         Coding        Complex
    task            task         reasoning
       ↓             ↓             ↓
   Fast model    Coding model   Strong model
```

This can reduce latency and API usage while reserving stronger models
for difficult work.

------------------------------------------------------------------------

# 18. External Tool Integration

June should eventually support external tools through APIs and/or
MCP-compatible interfaces.

Possible integrations:

``` text
GitHub
Docker
Kubernetes
AWS
Databases
Cloud services
Issue trackers
Documentation
CI/CD
```

The goal is to use APIs rather than browser automation whenever a
reliable API exists.

------------------------------------------------------------------------

# 19. Observability

June should log its internal activity.

Useful information:

``` text
Task ID
Model used
Tool used
Arguments
Execution time
Token usage
Errors
Retries
Files changed
Tests executed
Final status
```

This will make debugging June itself much easier.

------------------------------------------------------------------------


# 23. Multi-Agent Architecture

June is intended to use **multiple specialized agents/models**, rather than asking one model to perform every part of a coding task.

```text
                           JUNE
                             |
             +---------------+---------------+
             |               |               |
          PLANNER          CODER          RESEARCHER
             |               |               |
       Task reasoning    Code changes    Web/docs research
             |               |               |
             +---------------+---------------+
                             |
                         VERIFIER
                             |
                    Tests / checks / review
```

These are logical agent roles. They do not have to be separate Python processes. They can be separate model calls coordinated by `core/agent.py`.

## 23.1 Planner Agent

The Planner understands the user's goal and produces a structured execution plan.

Example:

```text
User:
"Add JWT authentication to this FastAPI project."

Planner:
1. Inspect project structure
2. Inspect existing authentication code
3. Inspect dependencies
4. Design authentication changes
5. Identify files to modify
6. Define verification steps
```

The Planner focuses on reasoning and decomposition rather than directly editing files.

## 23.2 Coder Agent

The Coder turns the plan into implementation.

Responsibilities:

- inspect relevant code
- create/edit files
- implement features
- fix bugs
- refactor code
- respond to tool results
- make iterative corrections

The Coder can use a fast coding-capable model when the task is concrete.

## 23.3 Researcher Agent

The Researcher handles information outside the repository.

Responsibilities:

- search documentation
- investigate APIs
- research package behavior
- investigate unfamiliar errors
- compare implementation approaches
- retrieve current technical information

The Researcher should return concise, relevant evidence to the Planner or Coder.

## 23.4 Verifier Agent

The Verifier independently checks whether the implementation actually works.

Possible checks:

```text
Run tests
   ↓
Run linting
   ↓
Run type checking
   ↓
Run build
   ↓
Inspect errors
   ↓
Inspect Git diff
   ↓
Return verification result
```

If verification fails:

```text
Verifier → failure information → Coder/Planner → new change → Verifier
```

This prevents June from assuming that generated code is correct.

## 23.5 Summarizer Agent

An optional lightweight model can handle:

- summarizing tool output
- summarizing long logs
- compressing conversation history
- creating memory entries
- producing the final user-facing summary

This avoids using expensive reasoning models for simple summarization.

# 24. Agent Coordination

`core/agent.py` coordinates the logical agents.

```text
User Request
     ↓
Agent
     ↓
Planner
     ↓
Execution Plan
     ↓
Coder
     ↓
Tools
     ↓
Tool Results
     ↓
Verifier
     ↓
 ┌───┴────┐
 │        │
FAIL    PASS
 │        │
 ↓        ↓
Coder   Final
 │
 ↓
Verifier
```

The system should repeat the Coder → Verifier cycle until:

1. the task succeeds,
2. a configured retry limit is reached,
3. human approval is required, or
4. June determines it cannot safely continue.

The Planner should be able to re-plan when new information changes the original assumptions.

# 25. Multiple Groq API Keys and Automatic Failover

June is intended to support **4–5 Groq API keys** for resilience and quota management.

The keys must **never be hard-coded in source code** and must never be committed to Git.

Example environment variables:

```text
GROQ_API_KEY_1
GROQ_API_KEY_2
GROQ_API_KEY_3
GROQ_API_KEY_4
GROQ_API_KEY_5
```

A key-manager component should load these securely.

The intended behavior is:

```text
Key 1
  ↓
request
  ↓
success
  ↓
continue using Key 1
```

If a request fails because the key is unavailable, expired, revoked, rate-limited, or its quota is exhausted:

```text
Key 1
  ↓
failure
  ↓
Key Manager
  ↓
Key 2
  ↓
retry request
```

The system can continue through the available keys:

```text
Key 1 → Key 2 → Key 3 → Key 4 → Key 5
```

The implementation must distinguish retryable key/quota/authentication failures from errors that should not simply be retried, such as malformed requests or invalid tool arguments.

Conceptually, the key manager should expose functionality similar to:

```python
get_available_key()
mark_key_failed(key)
mark_key_available(key)
execute_with_failover(request)
```

**Important:** key rotation is for availability and quota resilience. It must not be designed to bypass provider restrictions or account-level limits.

# 26. Model Routing vs API-Key Routing

These are two separate decisions.

### Model routing

Determines:

```text
Which model should perform this task?
```

Example:

```text
Planning       → stronger reasoning model
Coding         → coding-capable model
Summarization  → fast/cheap model
Verification   → reasoning model
Research       → appropriate reasoning/tool model
```

### API-key routing

Determines:

```text
Which available Groq credential should make the request?
```

Example:

```text
Coder → selected model → available Groq key
Planner → selected model → available Groq key
Verifier → selected model → available Groq key
```

Therefore:

```text
Agent Role
    ↓
Model Router
    ↓
Selected Model
    ↓
Groq Key Manager
    ↓
Available API Key
    ↓
Groq API
```

Model selection and credential failover should remain independent.

# 27. LLM-Readable Architecture Contract

These rules should be treated as architectural constraints whenever another LLM or coding agent works on June:

1. `main.py` is only the application entry point.
2. `core/agent.py` owns the main agent loop.
3. `models/` owns model/API communication.
4. `tools/` contains executable capabilities.
5. The LLM chooses tools and supplies structured arguments.
6. Python validates and executes tool calls.
7. The LLM must not directly execute arbitrary Python functions.
8. Safety/permission checks occur before risky tool execution.
9. Verification is separate from implementation.
10. Memory retrieval should provide relevant context rather than entire repositories.
11. Model selection is abstracted behind a model router.
12. Groq credentials are kept outside source code.
13. Groq API-key failover happens automatically for appropriate key/quota/authentication failures.
14. Multiple agent roles are coordinated by the core agent rather than hard-coded into individual tools.
15. Tools return structured results whenever practical.
16. Agent state is explicit and recoverable.
17. New tools are registered through a common tool interface/registry rather than a large chain of `if/elif` statements.
18. APIs/direct integrations are preferred over browser automation when reliable APIs exist.
19. Destructive operations require permission/approval according to the safety policy.
20. June verifies important changes before claiming a task is complete.

# 28. Target Capability

The long-term goal is for June to provide the capabilities expected from a modern autonomous coding agent.

A successful task should be able to look like:

```text
User
 ↓
Planner Agent
 ↓
Project/Memory Retrieval
 ↓
Research if required
 ↓
Coder Agent
 ↓
Filesystem / Terminal / Git / Other Tools
 ↓
Observe results
 ↓
Verifier Agent
 ↓
 ┌───────────────┐
 │               │
PASS            FAIL
 │               │
 ↓               ↓
Done        Re-plan / Fix
                 │
                 ↓
              Verify
```

June should therefore be a **general-purpose agent platform for software engineering**, not simply a Groq chatbot.


# 20. Development Roadmap

Do NOT build every module immediately.

## Phase 1 --- Minimal Agent

Build first:

``` text
main.py
models/groq_client.py
tools/filesystem.py
tools/terminal.py
```

Goal:

``` text
User → Groq → tool → result → Groq → answer
```

------------------------------------------------------------------------

## Phase 2 --- Coding Agent

Add:

``` text
Git
Code search
Test runner
Code analysis
Verification
```

Goal:

> June can modify a small repository and verify its changes.

------------------------------------------------------------------------

## Phase 3 --- Planning

Add:

``` text
agent.py
planner.py
executor.py
verifier.py
state.py
router.py
```

Goal:

> June can perform multi-step coding tasks autonomously.

------------------------------------------------------------------------

## Phase 4 --- Memory

Add:

``` text
episodic memory
semantic memory
vector store
retriever
```

Goal:

> June remembers useful project context across tasks.

------------------------------------------------------------------------

## Phase 5 --- Safety

Add:

``` text
permissions
approval
sandbox
```

Goal:

> June can operate autonomously without having unrestricted destructive
> access.

------------------------------------------------------------------------

## Phase 6 --- Advanced Capabilities

Add:

``` text
web search
parallel tools
model routing
MCP/external tools
process management
long-running tasks
```

------------------------------------------------------------------------

## Phase 7 --- User Interface

Add:

``` text
FastAPI backend
Web/Desktop UI
streaming
task status
approval UI
diff viewer
terminal output
```

------------------------------------------------------------------------

# 21. What "Antigravity-Level" Means for June

The target is not simply:

> "Generate code from a prompt."

June should eventually be able to:

-   understand an unfamiliar repository
-   create and modify files
-   search a codebase
-   run terminal commands
-   install dependencies
-   use Git
-   run tests
-   debug failures
-   inspect logs
-   iterate on failed solutions
-   perform multi-step tasks
-   research documentation
-   use external APIs/tools
-   maintain project memory
-   maintain task state
-   work autonomously within permission boundaries
-   ask for approval for risky actions
-   verify its own changes
-   explain what it changed
-   recover from failures
-   support long-running tasks
-   route work to appropriate models
-   execute independent operations in parallel

The important distinction is that **these capabilities emerge from the
agent loop + tools + verification + memory**, not from one giant prompt.

------------------------------------------------------------------------

# 22. Initial MVP

The first working version of June should NOT contain the entire
architecture.

Start with:

``` text
main.py
    ↓
Groq client
    ↓
tool-calling
    ↓
filesystem
    ↓
terminal
    ↓
tool result
    ↓
Groq
    ↓
final answer
```

Then progressively introduce planning, verification, Git, code search,
memory, safety, and advanced integrations.

**The goal is to grow June into the full architecture rather than trying
to implement the entire architecture on day one.**
