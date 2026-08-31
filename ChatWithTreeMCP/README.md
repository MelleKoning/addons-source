# ChatWithTreeMCP

ChatWithTreeMCP is a Gramplet Addon for Gramps.

The sources adhere to the Gramps GNU License - check the file headers for details.

## Explanation of the ChatWithTreeMCP Gramplet

The idea is to have an addon that uses Large Language Models (LLMs) to have a chat with your own genealogy tree. The Addon serves a few tools to interact with the genealogy tree database and uses an internal async interface to hand out defined tool calls to a running MCP.

For running local LLMs you could run an instance of [Ollama](https://ollama.com/blog/tool-support) or
you can use the stronger remote cloud LLMs, for exampe via OpenRouter, Anthrophic, MoonShotAI or any other.

## Short introduction

type `/help` in the chat to get rudimentary help

### Development documentation

`ChatWithTreeMCP.py` — The gramplet UI class for Gramps that embeds the chat panel, connects signals, and manages UI updates while interacting with the chat service.

`AsyncChatService.py` — Asynchronous service layer that orchestrates streaming chat interactions and emits incremental responses for UI consumption.

`chatwithllm.py` — Core chat logic defining an abstract IChatLogic interface and a ChatWithLLM implementation that talks to an LLM, including yield types for partial results and support for tool/function calling.

`ChatWithTreeMCP.gpr.py` — Gramps plugin registration file providing metadata and wiring to load the ChatWithTreeMCP gramplet.

`ChatWithTreeBot.py` — A chat logic implementation tailored for genealogy use that integrates with a Gramps database to answer questions about the user’s tree by implementing tools to interact with Gramps.

`.markdownlint.yaml` — Configuration for markdown linting rules used in this project.

`.pre-commit-config.yaml` — Pre-commit hook configuration (e.g., formatting, linting) to maintain code quality.

To execute run `pre-commit run -a` in the `/ChatWithTreeMCP` folder.

---

## Testing the plugin (backend, no GTK/UI)

Two Python environments are available for testing different Gramps versions:

- `chat_env` — Gramps 6.0.8 (database schema 18–21). Use with DBs matching that version (e.g. `GRAMPS_DB_NAME=Koning`).
- `chat_env_61` — Gramps 6.1.x (database schema 22, e.g. `"chatty"`). Create from the `maintenance/gramps61` branch (`python3.12 -m venv chat_env_61`, install `gramps` from that branch).

Run the integration test with either environment. The Gramps DB-loading plugins required by
`test_chat_service.py` are only available when the correct virtualenv is active; do not mix
environments. From `/ChatAddon` root:

```bash
# 6.0 test (nice-to-have)
source chat_env/bin/activate
export GRAMPS_DB_NAME="KoningGDriveBackup"   # or any DB matching schema 21
python -m pytest addons-source/ChatWithTreeMCP/tests/test_chat_service.py

# 6.1 / current work (chat_env_61 must be active)
source chat_env_61/bin/activate
export GRAMPS_DB_NAME="chatty"   # schema version 22 DB
export OPENCODE_API_KEY="<key>"
python -m pytest addons-source/ChatWithTreeMCP/tests/test_chat_service.py
```

`GRAMPS_DB_LOCATION` is optional; if omitted, the Gramps library (`CONFIGMAN`) provides the database path. The test requires a real LLM endpoint (`OPENCODE_API_KEY` for the default model).
