## Context

The app currently pins `@openai/agents` at `^0.0.5`. The target is `^0.5.2`, whose source is available read-only in `vendor/openai-agents-js/`. A previous unguided update attempt failed because the SDK's event handler signatures changed across several events without clear documentation. We now have two authoritative references:

- `docs/hob-architecture-baseline.md` — the functional contract each handler must preserve (Sections 5 and 9)
- `vendor/openai-agents-js/packages/agents-realtime/src/` — the exact new TypeScript types and event signatures

The update scope is deliberately narrow: bump versions, fix breakage, preserve all existing functional behavior exactly. No new features.

## Goals / Non-Goals

**Goals:**
- `package.json` reflects latest stable versions of all dependencies
- App compiles with zero TypeScript errors
- All functional guarantees in `docs/hob-architecture-baseline.md` are preserved post-update
- Each broken SDK event handler is fixed against the vendor source types

**Non-Goals:**
- Adopting new SDK features (MCP tools, `audio_start`/`audio_stopped` events, etc.)
- Changing any user-facing behavior
- Modifying anything in `vendor/` (read-only reference only)
- Migrating to a different transport (WebSocket vs WebRTC)

## Decisions

### 1. Fix event handlers one-by-one against vendor types, not in bulk

**Decision**: Each broken handler in `useHandleSessionHistory.ts` and `useRealtimeSession.ts` is fixed individually, with the vendor source type as the ground truth for the new signature, and the baseline doc as the ground truth for required behavior.

**Rationale**: Bulk search-and-replace risks missing subtle shape changes (e.g., `history_updated` now emits full history, not a delta). Isolating each fix makes regressions traceable to a specific handler.

**Alternative considered**: Keeping all handlers typed as `any` and relying on runtime behavior. Rejected — this is how the previous update silently broke things.

### 2. `agent_handoff`: use `toAgent.name` directly

**Decision**: Replace the `item.context.history` parse + `"transfer_to_"` string split with `toAgent.name` from the new third argument.

**Rationale**: The new signature is `(context, fromAgent, toAgent)`. The destination agent name is directly available on `toAgent.name`. The previous hack was a workaround for the old signature; it is no longer needed and no longer works.

**Baseline ref**: Section 5.12 — "SDK fires `agent_handoff` → extract agent name → `callbacks.onAgentHandoff(agentName)`"

### 3. `agent_tool_start` / `agent_tool_end`: use `tool.name` and `details.toolCall`

**Decision**: New signatures are `(context, agent, tool, details: {toolCall})` and `(context, agent, tool, result, details: {toolCall})`. Use `tool.name` for the function name and `details.toolCall.arguments` for the args.

**Rationale**: The previous `extractFunctionCallByName()` lookup against `details.context.history` was a workaround for not having the tool info directly. The new SDK passes it directly. The breadcrumb behavior (Section 5.9 of baseline) is unchanged.

### 4. `guardrail_tripped`: use `details.itemId` directly

**Decision**: Replace the history-search workaround (finding the last assistant message by scanning `details.context.history`) with `details.itemId` from the new fourth argument. Update the moderation extraction path to match the new `OutputGuardrailTripwireTriggered` error structure.

**Rationale**: The new signature is `(context, agent, error, details: {itemId})`. The `itemId` is directly provided, making the history scan both unnecessary and incorrect. The `sketchilyDetectGuardrailMessage()` regex in `handleHistoryAdded` remains valid — the guardrail feedback message format in `getRealtimeGuardrailFeedbackMessage()` (vendor source) still embeds `Failure Details: ${JSON.stringify(...)}`.

**Baseline ref**: Section 5.11 — `updateTranscriptItem(itemId, { guardrailResult: {...} })`

### 5. `history_updated`: reconcile by itemId, not treat as delta array

**Decision**: The new event emits the **full conversation history** as `RealtimeItem[]`, not just changed items. The handler must iterate the full array and call `updateTranscriptMessage` only for items that already exist in the transcript (by `itemId`) and whose text has changed.

**Rationale**: Blindly applying all items as updates would re-process finalized messages and cause flicker or duplicate content. The existing `transcriptItems` array (keyed by `itemId`) is the source of truth for what has been committed.

**Baseline ref**: Section 5.7 — "streaming updates mutate the single item in place via `itemId`"

### 6. `extractMessageText`: update content type discriminants

**Decision**: Change `c.type === 'audio'` to check for both `'input_audio'` (user messages) and `'output_audio'` (assistant messages), matching the new `RealtimeItem` Zod schemas in vendor source (`items.ts`).

**Rationale**: The old `'audio'` type no longer exists in the new SDK's item schema. Without this fix, transcripts for audio messages silently return empty strings.

### 7. Guardrail factory: adopt `defineRealtimeOutputGuardrail`

**Decision**: Rewrite `createModerationGuardrail` in `guardrails.ts` to use `defineRealtimeOutputGuardrail()` from `@openai/agents/realtime` (vendor: `guardrail.ts`). The existing `runGuardrailClassifier` logic that calls `/api/responses` is unchanged — only the wrapper that presents the result to the SDK changes.

**Rationale**: The old plain-object guardrail shape (`{ name, execute }` returning `{ tripwireTriggered, outputInfo }`) is no longer the expected interface. The SDK now expects an object conforming to `RealtimeOutputGuardrailDefinition`. Keeping the internal classifier logic unchanged reduces risk surface.

## Risks / Trade-offs

- **`history_updated` full-history reconciliation may miss edge cases** → Mitigation: only call `updateTranscriptMessage` for items already present in `transcriptItems` by `itemId`; do not create new items from this event (that responsibility stays with `history_added`).

- **Guardrail `outputInfo` path may differ** in `OutputGuardrailTripwireTriggered` vs the old `guardrail.result.output.outputInfo` path → Mitigation: consult vendor `guardrail.ts` and `realtimeSessionEvents.ts` for the exact error object shape before writing the fix.

- **TypeScript strict mode may surface additional type errors** beyond the known breaking changes → Mitigation: fix errors in dependency order (types.ts → hooks → agentConfigs → routes); do not suppress with `any` unless the vendor source itself uses `any` at that point.

- **`react` / `next` / `openai` base SDK updates may introduce unrelated breakage** → Mitigation: apply SDK fix and framework updates in separate commits so regressions are attributable; verify the `/api/responses` and `/api/session` routes compile cleanly against the new `openai` SDK.

## Migration Plan

1. **Update `package.json`** — bump all dependency versions; run `npm install`
2. **Fix TypeScript errors** in this order:
   a. `src/app/hooks/useHandleSessionHistory.ts` — `extractMessageText`, `handleHistoryUpdated`, `handleAgentToolStart`, `handleAgentToolEnd`, `handleGuardrailTripped`
   b. `src/app/hooks/useRealtimeSession.ts` — `handleAgentHandoff`
   c. `src/app/agentConfigs/guardrails.ts` — `createModerationGuardrail`
   d. `src/app/api/session/route.ts` and `src/app/api/responses/route.ts` — base `openai` SDK compatibility
3. **Verify `npm run build` passes** with zero errors
4. **Manual smoke test** each functional guarantee from the baseline (Section 5):
   - VAD speech → transcript (5.2, 5.3)
   - Interruption (5.4)
   - Tool invocation breadcrumb (5.9)
   - Guardrail trip → chip update (5.11)
   - Agent handoff breadcrumb (5.12)

**Rollback**: revert `package.json` and `package-lock.json` to the previous committed state; `npm install` restores the working version.

## Open Questions

- What is the exact field path to `moderationCategory` and `moderationRationale` within `OutputGuardrailTripwireTriggered` in the new SDK? Needs to be confirmed from vendor `guardrail.ts` + `agents-core` types before writing the `handleGuardrailTripped` fix.
- Does `history_updated` fire for user transcript updates (mid-speech) in v0.5.2, or is that now handled differently? If user speech deltas no longer come through `history_updated`, the `handleTranscriptionDelta` / `transport_event` path (Section 5.2 of baseline) must be verified still works.
