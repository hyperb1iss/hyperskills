# Conversation Format Reference

## Claude Code JSONL

**Location:** `~/.claude/projects/<encoded-path>/<session-uuid>.jsonl`
**Encoding:** Path separators replaced with `-` (e.g., `/Users/bliss/dev/dreamer` → `-Users-bliss-dev-dreamer`)

### Message Structure

Each line is a complete JSON object (one message per line):

```json
{
  "uuid": "unique-message-id",
  "parentUuid": "previous-message-uuid | null",
  "isSidechain": false,
  "type": "user | assistant | system | progress",
  "timestamp": "2026-04-04T22:15:00.000Z",
  "cwd": "/Users/bliss/dev/project",
  "sessionId": "session-uuid",
  "version": "2.1.81",
  "gitBranch": "main",
  "userType": "external",
  "entrypoint": "cli",
  "message": {
    "role": "user | assistant",
    "content": "..."
  }
}
```

### Content Formats by Role

**User messages:** `message.content` is a plain string (the prompt text).

**Assistant messages:** `message.content` is an array of typed blocks:

```json
[
  { "type": "thinking", "thinking": "internal reasoning...", "signature": "..." },
  { "type": "text", "text": "visible response..." },
  { "type": "tool_use", "id": "toolu_...", "name": "Bash", "input": { "command": "ls" } }
]
```

### Metadata Entries (Non-Message Lines)

These appear in the JSONL but aren't conversation messages:

| Type                    | Purpose                      | Key Fields                          |
| ----------------------- | ---------------------------- | ----------------------------------- |
| `summary`               | Compaction summary           | `leafUuid`, `summary`               |
| `ai-title`              | Auto-generated session title | `aiTitle`                           |
| `custom-title`          | User-set title               | `customTitle`                       |
| `tag`                   | Session tag                  | `tag`                               |
| `last-prompt`           | Last user prompt             | `lastPrompt`                        |
| `pr-link`               | Associated PR                | `prNumber`, `prUrl`, `prRepository` |
| `file-history-snapshot` | File state checkpoint        | `messageId`, `snapshot`             |
| `mode`                  | Coordinator/normal mode      | `mode`                              |
| `task-summary`          | Task summary                 | `summary`, `timestamp`              |

### Subagent Transcripts

**Location:** `<session-uuid>/subagents/agent-<agentId>.jsonl`
**Metadata:** `agent-<agentId>.meta.json` → `{agentType, description, worktreePath?}`

Subagent messages have `isSidechain: true` and an `agentId` field.

### Useful Grep Patterns

```bash
# All user prompts in a session (grep top-level type, not nested role)
grep '"type":"user"' session.jsonl | python3 -c "
import sys, json
for l in sys.stdin:
    obj = json.loads(l)
    content = obj.get('message', {}).get('content', '')
    if isinstance(content, str) and len(content) > 10 and not content.startswith('<'):
        print(content[:200])
"

# All tool invocations (inside assistant message content arrays)
grep '"tool_use"' session.jsonl | python3 -c "
import sys, json
for l in sys.stdin:
    obj = json.loads(l)
    for block in obj.get('message', {}).get('content', []):
        if isinstance(block, dict) and block.get('type') == 'tool_use':
            print(block.get('name', '?'), json.dumps(block.get('input', {}))[:100])
"

# Count messages by type
grep -c '"type":"user"' session.jsonl
grep -c '"type":"assistant"' session.jsonl

# Find error-containing tool outputs (from assistant tool_result blocks)
grep -i "error\|exception\|failed\|traceback" session.jsonl | head -20

# Find session title
grep '"ai-title"\|"custom-title"' session.jsonl

# Find thinking blocks (extended reasoning)
grep '"type":"thinking"' session.jsonl | wc -l
```

### Session Discovery

```bash
# All sessions for a project, sorted by recency
# Sessions live directly in the project dir, NOT in a sessions/ subdirectory
ls -lt ~/.claude/projects/-Users-bliss-dev-<project>/*.jsonl | head -20

# All projects with sessions in the last 7 days
# Exclude subagent transcripts which live in <session-uuid>/subagents/
find ~/.claude/projects -maxdepth 2 -name "*.jsonl" -not -path "*/subagents/*" -mtime -7 \
  | sed 's|/[^/]*\.jsonl$||' | sort -u

# Global history (all prompts across all projects)
tail -20 ~/.claude/history.jsonl | python3 -c "import sys,json; [print(json.loads(l).get('display','')[:100]) for l in sys.stdin]"

# Session sizes (bigger = richer conversations)
find ~/.claude/projects -maxdepth 2 -name "*.jsonl" -not -path "*/subagents/*" -mtime -7 \
  -exec ls -lhS {} + | head -20

# Get AI-generated session titles (great for understanding session topics)
for f in ~/.claude/projects/-Users-bliss-dev-*/*.jsonl; do
  title=$(grep -m1 '"ai-title"' "$f" 2>/dev/null | python3 -c "import sys,json; print(json.loads(next(sys.stdin)).get('aiTitle',''))" 2>/dev/null)
  [[ -n "$title" ]] && echo "$(du -h "$f" | cut -f1)  $(basename "$(dirname "$f")"): $title"
done | sort -rh | head -20
```

---

## Codex CLI JSONL

**Location:** `~/.codex/sessions/YYYY/MM/DD/rollout-<ISO-timestamp>-<session-uuid>.jsonl`

### Event Structure

Each line has a `timestamp`, `type`, and type-specific payload:

```json
{"timestamp": "2026-04-04T22:15:00Z", "type": "session_meta", ...}
{"timestamp": "2026-04-04T22:15:01Z", "type": "response_item", ...}
{"timestamp": "2026-04-04T22:15:02Z", "type": "event_msg", ...}
{"timestamp": "2026-04-04T22:15:03Z", "type": "turn_context", ...}
```

### Event Types

**`session_meta`** — One per file, session header:

- `payload.id`: Session UUID
- `payload.cwd`: Working directory
- `payload.cli_version`: CLI version
- `payload.originator`: `codex_cli_rs` | `codex_exec`
- `payload.model_provider`: Provider name (e.g., `openai`)
- `payload.base_instructions`: System prompt text (NOT `system_prompt`)
- `payload.source`: Source identifier
- `payload.git`: `{branch, origin_url, ...}` — git context for the session

**`response_item`** — Conversation turns:

- `payload.type`: `message` | `function_call` | `function_call_output` | `reasoning`
- For messages: `payload.role` = `developer` | `user` | `assistant`, `payload.content[].type` = `input_text` | `output_text`
- For function calls: `payload.name`, `payload.arguments` (JSON string), `payload.call_id`
- For function outputs: `payload.call_id`, `payload.output`
- For reasoning: `payload.encrypted_content` (opaque, not readable)

**`event_msg`** — Lifecycle events:

- `task_started`, `task_complete`, `token_count`, `user_message`, `agent_message`

**`turn_context`** — Per-turn metadata:

- `cwd`, `date`, `timezone`, `approval_policy`, `sandbox_policy`
- `model_name`, `personality`, `reasoning_effort`, `user_instructions`

### Useful Grep Patterns

```bash
# User messages from Codex
grep '"type":"event_msg"' rollout.jsonl | grep '"user_message"'

# Function calls (tool usage)
grep '"function_call"' rollout.jsonl | grep -v '"function_call_output"'

# Function outputs
grep '"function_call_output"' rollout.jsonl

# Assistant text responses
grep '"type":"response_item"' rollout.jsonl | grep '"output_text"'

# Session metadata
grep '"type":"session_meta"' rollout.jsonl

# Model being used
grep '"turn_context"' rollout.jsonl | head -1

# Session discovery
find ~/.codex/sessions -name "rollout-*.jsonl" -mtime -7 -exec ls -lhS {} + | head -20
```

### Codex SQLite (Supplementary)

**`~/.codex/state_5.sqlite`** — Thread index with columns:

- `id`, `title`, `model`, `cwd`, `git_branch`, `git_origin_url`
- `first_user_message`, `tokens_used`, `created_at`, `updated_at`

```bash
# List recent Codex threads
sqlite3 ~/.codex/state_5.sqlite "SELECT id, title, model, cwd, datetime(created_at, 'unixepoch') FROM threads ORDER BY created_at DESC LIMIT 20"
```

### Codex History (Supplementary)

**`~/.codex/history.jsonl`** — Flat prompt log:

```json
{ "session_id": "uuid", "ts": 1712300000, "text": "user prompt text" }
```

---

## Cross-Format Comparison

| Feature            | Claude Code                          | Codex                                    |
| ------------------ | ------------------------------------ | ---------------------------------------- |
| Location           | `~/.claude/projects/*/<uuid>.jsonl`  | `~/.codex/sessions/YYYY/MM/DD/*.jsonl`   |
| Message format     | `message.content` (string or array)  | `payload.content[].type`                 |
| Tool calls         | `type: "tool_use"` in content array  | `type: "function_call"` as response_item |
| Tool results       | Separate tool_result message         | `function_call_output` response_item     |
| Thinking/reasoning | `type: "thinking"` (readable)        | `type: "reasoning"` (encrypted)          |
| Session metadata   | `ai-title`, `tag`, `pr-link` entries | `session_meta` header + `turn_context`   |
| Subagents          | Separate `subagents/` directory      | Not applicable                           |
| Retention          | 30 days default                      | No auto-cleanup                          |
| Index DB           | None (JSONL only)                    | SQLite `state_5.sqlite`                  |
