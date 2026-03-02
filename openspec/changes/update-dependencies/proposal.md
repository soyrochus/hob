## Why

The app's key dependencies have moved significantly since the initial fork: `@openai/agents` has gone from v0.0.5 to v0.5.2 with breaking event-signature changes, and Next.js / React / the base `openai` SDK have newer releases. A previous update attempt caused regressions because the SDK's event contracts changed silently. We now have two reference sources that make a systematic update tractable: `docs/hob-architecture-baseline.md` (which documents the exact functional contracts each SDK event must satisfy) and `vendor/openai-agents-js/` (the full source of the target SDK version, used as read-only reference — it must not be modified).

## What Changes

- **BREAKING** Update `@openai/agents` from `^0.0.5` to `^0.5.x` — multiple event handler signatures changed (see Impact)
- Update `next` to latest stable (`^15.x`)
- Update `openai` (base SDK) to latest stable (`^4.x`)
- Update `react` / `react-dom` to latest stable (`^19.x`)
- Update remaining deps (`uuid`, `zod`, `react-markdown`, `@radix-ui/react-icons`, etc.) to latest compatible versions
- Fix all TypeScript and runtime breakage introduced by the above, guided by the baseline spec and vendor source

## Capabilities

### New Capabilities

None — this is a pure infrastructure update. No user-visible functionality is added or removed.

### Modified Capabilities

- `realtime-session-events`: The `@openai/agents/realtime` SDK event signatures changed between v0.0.5 and v0.5.2. All event handlers in `useRealtimeSession.ts` and `useHandleSessionHistory.ts` must be updated to match the new signatures while preserving the functional behavior documented in `docs/hob-architecture-baseline.md` Section 5 and Section 9.

## Impact

### Identified Breaking Changes in `@openai/agents` v0.0.5 → v0.5.2

The following are confirmed by reading `vendor/openai-agents-js/packages/agents-realtime/src/realtimeSessionEvents.ts` against the current handler signatures.

**`agent_handoff` event** (`useRealtimeSession.ts: handleAgentHandoff`):
- Old: `(item)` — agent name extracted by parsing `item.context.history` for a `"transfer_to_"` prefix
- New: `(context, fromAgent, toAgent)` — `toAgent.name` gives the destination agent name directly; no history parsing needed
- Required fix: replace history-parsing logic with `toAgent.name`

**`agent_tool_start` event** (`useHandleSessionHistory.ts: handleAgentToolStart`):
- Old: `(details, agent, functionCall)` — `details.context.history` was searched by name to get args
- New: `(context, agent, tool, details: { toolCall })` — `tool.name` and `details.toolCall.arguments` are directly available
- Required fix: update parameter destructuring; remove `extractFunctionCallByName` lookup

**`agent_tool_end` event** (`useHandleSessionHistory.ts: handleAgentToolEnd`):
- Old: `(details, agent, functionCall, result)`
- New: `(context, agent, tool, result, details: { toolCall })` — result is now the 4th param, tool info in `tool.name`
- Required fix: update parameter order and source of tool name

**`guardrail_tripped` event** (`useHandleSessionHistory.ts: handleGuardrailTripped`):
- Old: `(details, agent, guardrail)` — `itemId` found by searching history; moderation extracted via recursive `extractModeration()`
- New: `(context, agent, error: OutputGuardrailTripwireTriggered, details: { itemId })` — `details.itemId` is provided directly; moderation info is in `error.result.output.outputInfo`
- Required fix: use `details.itemId` directly; update moderation extraction path; remove history search

**`history_updated` event** (`useHandleSessionHistory.ts: handleHistoryUpdated`):
- Old: `(items: any[])` — treated as array of changed items
- New: `(history: RealtimeItem[])` — passes the **full** history on every update, not just changed items
- Required fix: handler must reconcile against existing transcript state rather than treating all items as new updates

**`RealtimeItem` content types** (`useHandleSessionHistory.ts: extractMessageText`):
- Old: checked for `c.type === 'audio'` to get transcripts
- New: user messages use `c.type === 'input_audio'`; assistant messages use `c.type === 'output_audio'`
- Required fix: update type checks in `extractMessageText` to `'input_audio'` and `'output_audio'`

**Guardrail definition API** (`guardrails.ts: createModerationGuardrail`):
- Old: plain object with `{ name, async execute({agentOutput}) }` returning `{ tripwireTriggered, outputInfo }`
- New: uses `defineRealtimeOutputGuardrail()` from `@openai/agents/realtime`, which wraps `defineOutputGuardrail` from `@openai/agents-core`; result shape follows `OutputGuardrailResult<RealtimeGuardrailMetadata>`
- Required fix: rewrite `createModerationGuardrail` using the new factory function

### Stable / Unaffected

The following are confirmed stable between versions (vendor source verified):

- `tool()` helper — still exported from `@openai/agents/realtime` (re-exported from `@openai/agents-core`); import path and signature unchanged
- `RealtimeSession` constructor shape — `new RealtimeSession(rootAgent, { transport, model, config, outputGuardrails, context })` unchanged
- `session.connect({ apiKey, url? })` — unchanged
- `session.interrupt()`, `session.mute()`, `session.sendMessage()`, `session.close()` — unchanged
- `transport_event` routing — still the mechanism for `conversation.item.input_audio_transcription.completed`, `response.audio_transcript.delta`, `response.audio_transcript.done`
- `history_added` event — still `(item: RealtimeItem)`; item structure compatible
- `OpenAIRealtimeWebRTC` with `changePeerConnection` hook — unchanged
- `/api/session` and `/api/responses` routes — no SDK dependency; affected only by `openai` base SDK updates

### Reference Sources

- **Correctness contract**: `docs/hob-architecture-baseline.md` — defines what each handler must do functionally (Sections 5 and 9). Any fix must preserve these guarantees.
- **Target API**: `vendor/openai-agents-js/packages/agents-realtime/src/` — read-only source of truth for new event signatures, types, and factory functions. Do not modify files in `vendor/`.

### Affected Files

| File | Reason |
| ---- | ------ |
| `package.json` | Version bumps |
| `src/app/hooks/useRealtimeSession.ts` | `agent_handoff` handler; connect options |
| `src/app/hooks/useHandleSessionHistory.ts` | `agent_tool_start/end`, `guardrail_tripped`, `history_updated`, `extractMessageText` |
| `src/app/agentConfigs/guardrails.ts` | Guardrail definition API rewrite |
| `src/app/api/responses/route.ts` | `openai` base SDK API compatibility |
| `src/app/api/session/route.ts` | `openai` base SDK API compatibility |
