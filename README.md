# Personal assistant with long-term memory

A macOS assistant you can **talk to** (microphone + speech) or **chat
with** in the terminal. It uses OpenAI tool calling to open apps and
websites and to search, and it **remembers facts about you** across
conversations, with versioning, conflict handling, and an audit log.

```
╭──────────────────────────────── Assistant ────────────────────────────────╮
│ Chat with your assistant. It can open apps and websites, search, and      │
│ remember facts about you.                                                 │
│ Type /help for commands, /quit to exit.                                   │
╰───────────────────────────────────────────────────────────────────────────╯

You › /remember I prefer Python
✓ Saved as 3f9c2a1b.

You › /remember my password is hunter2
✗ Refusing to store sensitive data in memory (password).
```

## Quick start

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # install dependencies
cp chatting/.env.example chatting/.env    # then set OPENAI_API_KEY

uv run python chatting/main.py --text     # text chat
uv run python chatting/main.py            # voice mode (needs a microphone)
```

Voice mode needs PortAudio for the microphone (`brew install portaudio`).

## Chat commands

| Command                   | What it does                                  |
| ------------------------- | --------------------------------------------- |
| `/memories [search]`      | List saved memories, or search them           |
| `/remember <fact>`        | Save a fact                                   |
| `/forget <id>`            | Delete a memory (asks first)                  |
| `/history <id>`           | Show earlier versions of a memory             |
| `/restore <id> <version>` | Bring back an earlier version                 |
| `/stats`                  | Memory and tool statistics                    |
| `/clear`                  | Start a new conversation (memories are kept)  |
| `/help`, `/quit`          | Help, exit                                    |

IDs can be shortened to their first few characters, as shown in
`/memories`.

## How it works

```
             you
              │  text or speech
              ▼
   ┌─────────────────────┐   interfaces/text_chat.py, interfaces/voice.py
   │      Interface      │
   └──────────┬──────────┘
              ▼
   ┌─────────────────────┐   agent.py
   │        Agent        │── 1. save facts ──────────► MemoryManager
   │  (tool-call loop)   │── 2. recall memories ─────► MemoryManager
   │                     │── 3. ask the model ───────► OpenAI
   │                     │── 4. run tools ───────────► ToolExecutor
   └─────────────────────┘
```

Saving a memory (`MemoryManager.upsert`) runs a small pipeline:

1. **Guard**: reject empty, oversized, or sensitive content.
2. **Candidates**: find related memories (same key first, then
   semantic search reranked by importance and recency).
3. **Resolve**: decide whether the new fact is new, a duplicate, an
   update, or a contradiction. Done by the AI, with a rule-based
   fallback when OpenAI is unavailable or answers invalidly.
4. **Policy**: decide what to do; uncertain or conflicting updates
   ask you first.
5. **Store**: save; the old version goes to history.
6. **Event**: logged, counted (`/stats`), and written to the audit log.

## Safety

- **Secrets are never stored.** API keys, passwords, card numbers,
  SSNs, and private keys are rejected before reaching memory or the AI
  resolver, and the assistant tells you it did not save them.
- **Logs and the audit trail are redacted**, including tracebacks.
- **Memories are treated as data, not instructions**, so a stored
  "ignore your rules…" cannot steer the model.
- **Risky tools ask first** (for example opening Terminal); blocked
  risk levels never run.
- **Tool limits**: per-call timeout, 20 calls per minute, and size
  limits on arguments and results.
- **URLs** are restricted to `http`/`https`.

Detection is pattern based. It catches common, well-formed secrets,
but it is not a guarantee: avoid typing secrets into the chat.

## Project layout

```
chatting/
├── main.py                 entry point (--text / --voice)
├── config/                 settings (.env) and logging
├── services/               OS integrations: apps, browser, speech, TTS
├── assistant/
│   ├── agent.py            model + tool-calling loop
│   ├── factory.py          builds and connects everything
│   ├── application.py      startup checks, run, shutdown
│   ├── interfaces/         text chat, chat commands, voice loop
│   ├── safety/             secret detection, text cleaning
│   ├── tools/              registry, executor, permissions, limits
│   └── memory/
│       ├── manager.py      the memory workflow
│       ├── guard.py        what may be stored
│       ├── storage/        where memories live (Chroma, in-memory)
│       ├── retrieval/      semantic search and candidate ranking
│       ├── resolution/     AI + rule-based conflict resolution
│       ├── history/        previous versions, rollback
│       ├── events/         logging, metrics, and audit listeners
│       └── audit/          audit records
├── tests/                  pytest suite (no network, no API costs)
├── data/memory/            memory database (git-ignored)
└── logs/                   assistant.log (git-ignored)
```

## Development

```bash
uv run pytest             # run the tests (no network or API calls)
ruff check chatting       # lint
mypy                      # type-check
```

All three are configured in `pyproject.toml` and run from the
repository root.

## Configuration

All settings live in `chatting/.env`; see
[`chatting/.env.example`](chatting/.env.example) for every option
with explanations.
