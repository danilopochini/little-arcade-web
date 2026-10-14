# VS Code AI Testing (Test Companion extension)

The Test Companion VS Code extension and its webview. It drives tasks, executes tools locally, and speaks the router's wire contract.

## Language

**Task**:
One conversation with its own history and checkpoints.

**MCP native lane**:
The request shape in which MCP reaches the model as natively declared tools: the extension sends the manifest and omits its XML `# Connected MCP Servers` section. Gated on `native_tool_calling`, read from the task's flag snapshot. Defined in `llm_router/CONTEXT.md`.
_Avoid_: protocol v2, v2 lane, API version

**Provider block**:
A content block received from the router as an opaque chunk and stored in the assistant message without interpretation.
_Avoid_: search result, tool search block

**Off-lane resume**:
Resuming a task while the native lane is off: provider blocks are stripped from the stored history, because nothing is left to expand a `tool_reference`.
_Avoid_: downgrade, rollback

**API conversation history**:
The Anthropic-shaped message list persisted per task and sent whole on every request.
_Avoid_: transcript, chat log

**MCP tool manifest**:
The list of tools from advertisable MCP servers, sent only on native-lane parent requests.

**Advertisable server**:
A connected MCP server whose tools pass curation and the per-tool denylist, so the manifest and the XML prompt section always describe the same set.

**Condense**:
The whole-message range delete plus overlay rewrite that shrinks history when the context fills.
_Avoid_: truncation, compaction

**Flavour pin**:
The Sonnet 5.5 behaviour set a task is frozen to when it starts, persisted with the task and inherited by its children.
_Avoid_: flavour flag, live flavour, task mode

**Flags wait**:
The bounded wait (5 seconds) a new task makes for the account's flags when none are stored, so the flavour pin is decided on real flags. Never on the CLI or the cloud brain.
_Avoid_: flag poll, startup delay

**Completion gate cap**:
The ceiling on how many times the test-fix completion gate refuses a completion for missing or failed run evidence before it releases the task as unverified.
_Avoid_: retry limit, refusal budget, gate timeout

**Long-command handoff**:
Returning control to the model while a foreground command is still running, after long silence or long total time, with the command left alive.
_Avoid_: timeout, detach, kill, command abort

**Wake scope**:
The set of parked asks that a command exit or heartbeat may resume, which is the asks the model raised itself.
_Avoid_: wake list, auto-answer

**Masked key token**:
The fixed placeholder `<BROWSERSTACK_KEY_MASKED>` that stands in for the registered BrowserStack key in everything the model reads.
_Avoid_: redacted key, hidden key, key placeholder

**Unflagged change**:
A Sonnet 5.5 release change that reaches every user because its impact is minimal or it is a direct improvement. Each one is listed in the umbrella flag's doc comment and the changelog.
_Avoid_: silent change, ungated change, hotfix
