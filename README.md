# AI Coding Agent

A production-grade, multi-provider AI coding agent that can autonomously read project context, work through issue backlogs, write code, run commands, and manage its own memory — all while following your project's specific coding standards and terminology.

## 🎯 Overview

This is a **spec-driven AI coding agent** built from scratch in Python. Unlike generic coding assistants, this agent:

- Reads your project's glossary, coding standards, and architecture docs before writing code
- Works through an issue backlog autonomously (Definition of Ready → In Progress → Done)
- Uses surgical file edits (`str_replace_file`) to save tokens and prevent errors
- Supports multiple LLM providers (Groq, Anthropic, NVIDIA) via a clean factory pattern
- Manages its own memory with zero-cost history trimming
- Tracks tokens, latency, and tool usage via JSONL observability logs
- Recovers gracefully from crashes and rate limits
- Orchestrates multiple worker agents via a Tech Lead pattern

## ✨ Features

### Core Agent Capabilities
- **File Operations**: Read, write, append, and surgically edit files via `str_replace_file`
- **Shell Commands**: Execute commands in a sandboxed environment with approval gates
- **Context Loading**: Automatically reads project specs before acting
- **Issue-Driven Workflow**: Picks up issues, checks dependencies, marks them done
- **Human-in-the-Loop**: Configurable approval system for risky actions

### Advanced Features
- **Multi-Provider LLM Support**: Switch between Groq, Anthropic, and NVIDIA via environment variables
- **Tech Lead Mode**: Orchestrates multiple worker agents to parallelize issue resolution
- **Zero-Cost Memory Management**: Sliding window history trimming (no LLM summarization overhead)
- **Automated Syntax Validation**: Python files are syntax-checked immediately after writing
- **Crash Recovery**: Saves state to disk; resume interrupted sessions with `resume` command
- **JSONL Observability**: Tracks tokens, latency, and tool success/failure rates per run
- **Spec Amendment Protocol**: Versioned context files with changelog-driven adaptation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py (CLI)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    agent/core.py (Agent)                     │
│  - Conversation loop                                         │
│  - History management (trimming)                             │
│  - Tool execution with retries                               │
│  - Observability tracking                                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  agent/llm   │    │  agent/tools     │    │agent/approval│
│  (Factory)   │    │  (File, Command) │    │              │
└──────────────┘    └──────────────────┘    └──────────────┘
        │
        ├─► GroqLLMClient
        ├─► AnthropicLLMClient
        └─► NvidiaLLMClient
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- API key(s) for at least one LLM provider

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-coding-agent

# Install dependencies (creates .venv and installs from pyproject.toml)
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### Required Dependencies

The project depends on the following packages (managed via `pyproject.toml`):

- `groq` — For Groq provider
- `anthropic` — For Anthropic/Claude provider
- `openai` — For NVIDIA NIM (OpenAI-compatible)
- `python-dotenv` — For environment variable loading

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider to use (`groq`, `anthropic`, or `nvidia`) | `groq` |
| `API_KEY` | API key for the selected provider | *(required)* |
| `LLM_MODEL` | Model name (e.g., `claude-3-5-sonnet-20241022`) | `qwen/qwen3.8-27b` |
| `LLM_MAX_TOKENS` | Max output tokens per response | `2000` |
| `LLM_TEMPERATURE` | Sampling temperature | `0.3` |
| `PROJECT_ROOT` | Path to the project the agent works on | `./target-project` |
| `APPROVAL_MODE` | Approval mode: `smart`, `always`, or `never` | `smart` |
| `MAX_HISTORY_LENGTH` | Max messages before history trimming | `10` |

## 🚀 Usage

### Interactive Mode

```bash
uv run main.py
```

You'll be prompted to enter a message. The agent will then iteratively call tools to fulfill your request.

#### Available Commands
- Type any prompt to interact with the agent
- `quit` / `exit` / `q` — Exit the agent
- `reset` — Clear conversation history
- `resume` — Continue from a saved state (after crash or restart)

### Tech Lead Mode

Orchestrate multiple worker agents to work through the issue backlog:

```bash
uv run main.py --tech-lead "Complete the backend issues"
```

The Tech Lead will:
1. Discover available issues via `list_issues`
2. Filter by dependencies and Definition of Ready
3. Delegate each issue to a fresh worker agent
4. Generate a summary of completed/failed work

## 📁 Target Project Setup

The agent works on a **target project** (configured via `PROJECT_ROOT`). This is the codebase the agent will read from and write to.

### Project-Agnostic Design

The agent is **not tied to any specific directory structure**. It discovers your project's layout by listing directories and reading files. Whether your project uses `src/`, `lib/`, `app/`, or a flat structure, the agent adapts.

You simply point it at a project and give it a task. It will:
- Explore the existing structure via `list_directory`
- Read relevant files to understand the codebase
- Create new files and directories as needed to fulfill your request

### Optional Conventions

While not required, the agent supports some optional conventions that unlock advanced features:

- **`context/` folder** — If present, the agent reads project specifications (glossary, coding standards) from here before writing code. This ensures the agent follows your project's terminology and style rules.
- **`issues/` folder** — If present, the agent can work through an issue backlog autonomously, picking up tasks, checking dependencies, and marking them done.
- **`logs/` folder** — Auto-created by the agent to store JSONL observability logs.

These are **conventions, not requirements**. The agent works perfectly well without any of them — you just lose the corresponding advanced features.

### Example Templates

To help you adopt these conventions, example templates are provided in `agent/templates/`. These templates demonstrate the expected format for versioned context files, issue tracking, and changelog entries.

To use these templates in your target project:

```bash
# Copy example context files (optional)
cp -r agent/templates/context/* target-project/context/

# Copy example issues (optional)
cp -r agent/templates/issues/* target-project/issues/
```

This gives you a starting point with:
- Versioned context files with YAML frontmatter
- Issue files with Definition of Ready, Acceptance Criteria, and dependency tracking
- Changelog entries for spec amendments

## 🛠️ Available Tools

The agent has access to these tools:

| Tool | Description |
|------|-------------|
| `read_file` | Read the contents of a file |
| `write_file` | Create or overwrite a file (with syntax validation) |
| `append_to_file` | Append content to the end of a file |
| `str_replace_file` | Surgically replace a specific block of text |
| `list_directory` | List files and directories |
| `list_context_files` | Discover available project specs |
| `list_issues` | List issues with optional status filtering |
| `update_issue_status` | Update an issue's status (backlog/in_progress/done/blocked) |
| `check_spec_versions` | Check current versions of all context files |
| `run_command` | Execute a shell command (with approval) |

## 🧠 How It Works

### The Agent Loop

1. User provides a prompt
2. Agent adds prompt to history
3. While iteration < max_iterations:
   - Trim history if too long (zero-cost sliding window)
   - Send history + tools to LLM
   - Track LLM response (tokens, latency)
   - If tool calls present: execute each tool, track metrics, save state, append results to history
   - If no tool calls: return final response, clear saved state

### Memory Management

The agent uses a **sliding window** approach:
- **Always preserved**: System prompt + first user message + last 4 messages
- **Trimmed**: Everything in between when history exceeds `MAX_HISTORY_LENGTH`
- **Zero cost**: Pure Python list slicing, no LLM calls

This forces the agent to rely on the filesystem (`read_file`) for long-term context rather than stale conversation history.

### Approval System

Three modes controlled by `APPROVAL_MODE`:
- **`smart`** (default): Asks for approval on file writes and shell commands
- **`always`**: Asks for approval on every action
- **`never`**: No approval required (use with caution)

## 🔌 Multi-Provider Support

### Switching Providers

Update the `LLM_PROVIDER` and `API_KEY` in your `.env` file. The agent will automatically use the corresponding client.

### Adding a New Provider

1. Create a new class in `agent/llm.py` inheriting from `BaseLLMClient`
2. Implement the `complete()` method
3. Add a branch in the `create_llm_client()` factory
4. Update `.env` with the new provider name

## 🔄 Spec Amendment Protocol

Project specs are versioned using YAML frontmatter. When specs change:

1. Bump the version in the file's frontmatter
2. Add an entry to `context/CHANGELOG.md` describing the change, impact, and migration steps
3. The agent will detect the version change via `check_spec_versions` and adapt automatically

See `agent/templates/context/CHANGELOG.md` for the expected format.

## 📊 Observability

Every run generates a JSONL log in `target-project/logs/`. Each log file contains structured events including:

- `run_start` / `run_end` — Session boundaries with total tokens and duration
- `user_prompt` — The user's input
- `llm_response` — Token usage per LLM call
- `tool_call` — Tool name, arguments, success state, and latency

These logs can be ingested by observability platforms like Langfuse, Braintrust, or Datadog, or analyzed locally with any JSON parser.

## 🐛 Troubleshooting

### Rate Limit Errors (429)

**Symptom**: `Rate limit reached for model...`

**Solutions**:
1. Switch to a different provider in `.env`
2. Wait for the cooldown period (shown in error message)
3. Upgrade to a paid tier for higher limits
4. Reduce `LLM_MAX_TOKENS` to use fewer tokens per request

### Input Token Limit (413)

**Symptom**: `Request too large... on input tokens per minute`

**Solutions**:
1. Reduce `MAX_HISTORY_LENGTH` in `.env` (try 6-8)
2. The agent already truncates tool outputs to 800 chars automatically
3. Start a fresh session with `reset` command

### Agent Stuck in Loop

**Symptom**: `Agent exceeded maximum iterations (40)`

**Solutions**:
1. Check if the agent is hitting repeated errors (view logs in `target-project/logs/`)
2. Provide more specific instructions
3. Increase `max_iterations` in `agent/core.py` if needed
4. Use `reset` to clear history and try again

### Crash Recovery

If the agent crashes or you hit `Ctrl+C`:
1. State is automatically saved to `target-project/.agent_state.json`
2. Restart the agent with `uv run main.py`
3. Type `resume` to continue from where it left off

## 📁 Project Structure

```
ai-coding-agent/
├── main.py                      # CLI entry point
├── config.py                    # Configuration management
├── pyproject.toml               # Project dependencies
├── .env                         # Environment variables (create this)
├── prompts/
│   └── system.md                # Agent system prompt
├── agent/
│   ├── core.py                  # Agent class (main loop)
│   ├── llm.py                   # Multi-provider LLM clients
│   ├── approval.py              # Human-in-the-loop approval
│   ├── observability.py         # JSONL logging
│   ├── tech_lead.py             # Multi-agent orchestrator
│   ├── templates/               # Example files (optional conventions)
│   │   ├── context/             # Example context files
│   │   └── issues/              # Example issue files
│   └── tools/
│       ├── __init__.py          # Tool exports
│       ├── base.py              # Tool base class
│       ├── file_tools.py        # File operations
│       └── command_tools.py     # Shell command execution
└── target-project/              # Any project you point the agent at
    └── (agent discovers and adapts to whatever structure exists here)
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Parallel multi-agent execution (asyncio)
- Web UI for monitoring
- CI/CD integration
- Additional LLM providers (OpenAI, Mistral, local Ollama)
- Enhanced tool capabilities (search, git operations)

## 📄 License

MIT License — see LICENSE file for details.

## 🙏 Acknowledgments

Inspired by production AI coding tools like Cursor, Aider, Devin, and SWE-agent. Built to demonstrate the architecture behind modern AI coding agents.