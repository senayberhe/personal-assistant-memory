# Long-term memory

This package lets the assistant remember facts about you across
conversations, and keep them correct as they change.

The hard part is not storing facts but keeping them up to date. If
you say "I prefer tea" today and "I prefer coffee" next month, a
plain vector store keeps both. Here, the second fact is recognised
as a contradiction, you are asked, and the old version is kept in
history so it can be restored.

```python
from assistant.memory import MemoryManager

manager.upsert(content="I prefer Python", memory_type="preference")
manager.recall_ranked("which language do I like?", top_k=5)
```

`MemoryManager` (`manager.py`) is the single entry point. It owns the
workflow and hands each step to a small, replaceable class.

## Saving a memory: `upsert`

```
 new fact
    │
    ▼
 1. Guard ──────────── reject empty, > 1,000 chars, or secrets
    │
    ▼
 2. Find candidates ── same key first, then semantic search,
    │                  reranked by importance and recency
    ▼
 3. Resolve ────────── CREATE · UPDATE · IGNORE · CONTRADICT · UNRELATED
    │                  (AI first, rule-based fallback)
    ▼
 4. Policy ─────────── what to do; ask the user when unsure
    │
    ▼
 5. Store ──────────── save; the old version goes to history
    │
    ▼
 6. Event ──────────── logging · metrics (/stats) · audit log
```

| Step | Module | Notes |
| ---- | ------ | ----- |
| 1. Guard | `guard.py` | Raises `SensitiveMemoryError` for secrets, using `assistant.safety` |
| 2. Candidates | `retrieval/` | `candidate_retriever.py` finds, `candidate_ranker.py` reranks |
| 3. Resolve | `resolution/` | `ai.py` asks the model; `rules.py` is the fallback; `resilient.py` switches between them |
| 4. Policy | `policy.py` | Contradictions and updates under 0.80 confidence need confirmation |
| 5. Store | `storage/`, `history/` | ChromaDB on disk, or in-memory for tests |
| 6. Event | `events/`, `audit/` | A publisher fans out to logging, metrics and audit listeners |

### Resolver vs. policy

The two are kept apart on purpose:

- the **resolver** answers *"What is this memory?"*
- the **policy** answers *"What should we do with it?"*

Neither touches storage, so each can be tested on its own.

| Resolution   | Policy action | Asks you?                  |
| ------------ | ------------- | -------------------------- |
| `CREATE`     | create        | no                         |
| `UNRELATED`  | create        | no                         |
| `IGNORE`     | nothing       | no (it is a duplicate)     |
| `UPDATE`     | update        | only if confidence < 0.80  |
| `CONTRADICT` | update        | always                     |

### When OpenAI is unavailable

`ResilientMemoryResolver` tries `AIMemoryResolver` first. The AI's
answer is validated with a Pydantic schema (`resolution/schema.py`).
It falls back to the rule-based `MemoryResolver` when the API times
out, cannot connect, is rate-limited, or returns an invalid answer
(for example a memory ID that does not exist).

The rules are deliberately simple and predictable:

- identical text (ignoring case and spaces) → `IGNORE`
- "I like X" vs "I don't like X" (also *prefer* and *use*) → `CONTRADICT`
- at least 50% word overlap → `UPDATE` (confidence 0.75, so you are asked)
- otherwise → `UNRELATED`

## Recalling memories

`recall_ranked` scores each match (`ranking.py`):

```
score = 0.60 × similarity + 0.25 × importance + 0.15 × recency
recency = exp(-age_in_days / 30)
```

The agent adds the top 5 to the model's instructions on every
message. Expired memories (`expires_at`, see `lifecycle.py`) are
skipped and can be removed with `cleanup_expired`.

### Memories are data, not instructions

`context.py` wraps recalled memories in a `<memories>` block that the
model is told to treat as untrusted data. Any `<memories>` tags inside
stored text are removed first, so a saved "ignore your rules…" cannot
escape the block.

## History and rollback

Every update stores the previous version (`history/`). From the chat:

```
/history 3f9c        # list earlier versions
/restore 3f9c 2      # bring back version 2
```

Restoring is itself a new version, so nothing is ever lost.

## Other modules

| Module | Purpose |
| ------ | ------- |
| `model.py` | The `Memory` dataclass: content, type, importance, key, version, expiry |
| `extractor.py` | Spots facts worth saving in a message ("remember that…", "I prefer…") |
| `confirmation.py` | Asks the user yes/no before saving or changing a memory |
| `conversation.py` | Short-term chat history (cleared by `/clear`; long-term memory is kept) |
| `embeddings.py` | OpenAI embeddings, plus a simple offline version for tests |
| `similarity.py`, `deduplicator.py` | Similarity helpers and duplicate detection |

## Storage backends

Every store has two implementations behind the same interface
(`base.py` in each folder):

| Folder | ChromaDB (real use) | In-memory (tests) |
| ------ | ------------------- | ----------------- |
| `storage/` | `chroma.py` | `in_memory.py` |
| `retrieval/` | `chroma.py` | `in_memory.py` |
| `history/` | `chroma.py` | `in_memory.py` |
| `audit/` | `chroma.py` | `in_memory.py` |

`assistant/factory.py` picks the ChromaDB versions and connects
everything. Data is saved in `chatting/data/memory/`, which git
ignores.

## Tests

The memory tests are in `chatting/tests/test_memory_*.py`, plus
`test_ai_memory_*`, `test_chroma_*` and `test_safety_contract.py`.
None of them make network calls:

```bash
uv run pytest -k memory
```
