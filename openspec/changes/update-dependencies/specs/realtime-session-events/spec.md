## MODIFIED Requirements

### Requirement: agent_handoff event handler derives agent name from event argument

The system SHALL derive the destination agent name directly from the `toAgent` argument of the `agent_handoff` event rather than parsing conversation history.

The `agent_handoff` event signature in `@openai/agents/realtime` v0.5.x is:
`(context, fromAgent, toAgent)` where `toAgent.name` is the destination agent name.

#### Scenario: Agent handoff updates selected agent name

- **WHEN** the SDK fires `agent_handoff` with `(context, fromAgent, toAgent)`
- **THEN** `handleAgentHandoff` reads `toAgent.name` as the destination agent name
- **THEN** `callbacks.onAgentHandoff(toAgent.name)` is called
- **THEN** no history parsing or string splitting is performed

---

### Requirement: agent_tool_start event handler reads tool info from event arguments

The system SHALL read the tool name and arguments directly from the `tool` and `details.toolCall` arguments of the `agent_tool_start` event.

The `agent_tool_start` event signature is: `(context, agent, tool, details: { toolCall })`.

#### Scenario: Tool start breadcrumb is added with correct name and args

- **WHEN** the SDK fires `agent_tool_start` with `(context, agent, tool, details)`
- **THEN** `handleAgentToolStart` uses `tool.name` as the function name
- **THEN** `handleAgentToolStart` uses `details.toolCall.arguments` as the function arguments
- **THEN** `addTranscriptBreadcrumb("function call: {tool.name}", arguments)` is called
- **THEN** no lookup into `context.history` is performed to find the tool call

---

### Requirement: agent_tool_end event handler reads tool info from event arguments

The system SHALL read the tool name and result directly from the `tool` and `result` arguments of the `agent_tool_end` event.

The `agent_tool_end` event signature is: `(context, agent, tool, result, details: { toolCall })`.

#### Scenario: Tool end breadcrumb is added with correct name and result

- **WHEN** the SDK fires `agent_tool_end` with `(context, agent, tool, result, details)`
- **THEN** `handleAgentToolEnd` uses `tool.name` as the function name
- **THEN** `handleAgentToolEnd` uses `result` (string) as the tool result
- **THEN** `addTranscriptBreadcrumb("function call result: {tool.name}", parsedResult)` is called
- **THEN** no lookup into `context.history` is performed

---

### Requirement: guardrail_tripped event handler uses itemId from event argument

The system SHALL use the `itemId` provided directly in `details.itemId` from the `guardrail_tripped` event to identify the offending transcript item. It SHALL NOT search conversation history to find the last assistant message.

The `guardrail_tripped` event signature is: `(context, agent, error: OutputGuardrailTripwireTriggered, details: { itemId })`.

#### Scenario: Guardrail trip updates the correct transcript item

- **WHEN** the SDK fires `guardrail_tripped` with `(context, agent, error, details)`
- **THEN** `handleGuardrailTripped` reads `details.itemId` as the target item ID
- **THEN** `updateTranscriptItem(details.itemId, { guardrailResult: {...} })` is called
- **THEN** no history scan is performed to find the offending message

#### Scenario: Guardrail corrective message is still detected as breadcrumb

- **WHEN** the SDK injects a corrective message into history after a guardrail trip
- **THEN** `handleHistoryAdded` detects the `"Failure Details: {...}"` pattern via `sketchilyDetectGuardrailMessage()`
- **THEN** the corrective message is added as a `BREADCRUMB`, not a `MESSAGE`

---

### Requirement: history_updated event handler reconciles full history against existing transcript

The system SHALL treat the payload of `history_updated` as the full conversation history and update only transcript items that already exist (matched by `itemId`). It SHALL NOT create new transcript items from this event.

The `history_updated` event signature is: `(history: RealtimeItem[])` — the full history array, not a delta.

#### Scenario: In-progress item text is updated from history

- **WHEN** the SDK fires `history_updated` with the full history
- **THEN** `handleHistoryUpdated` iterates all items in the history array
- **THEN** for each item whose `itemId` exists in `transcriptItems`, text is updated via `updateTranscriptMessage(itemId, text, false)` (replace mode)
- **THEN** no new `TranscriptItem` is created for items not already in `transcriptItems`

#### Scenario: Already-finalized items are not re-processed

- **WHEN** `history_updated` fires after a turn is finalized (`status: DONE`)
- **THEN** the handler does not overwrite the finalized text with stale history content

---

### Requirement: extractMessageText handles updated content type discriminants

The system SHALL correctly extract transcript text from `RealtimeItem` content using the content type discriminants of `@openai/agents/realtime` v0.5.x.

In v0.5.x, user audio content has `type: 'input_audio'` and assistant audio content has `type: 'output_audio'`. The old `type: 'audio'` discriminant no longer exists.

#### Scenario: User audio transcript is extracted from input_audio content

- **WHEN** a user `RealtimeItem` contains a content entry with `type: 'input_audio'`
- **THEN** `extractMessageText` returns the `transcript` field of that entry

#### Scenario: Assistant audio transcript is extracted from output_audio content

- **WHEN** an assistant `RealtimeItem` contains a content entry with `type: 'output_audio'`
- **THEN** `extractMessageText` returns the `transcript` field of that entry

#### Scenario: Items with no audio transcript return empty string

- **WHEN** a `RealtimeItem` contains only `input_text` or `output_text` content (no audio)
- **THEN** `extractMessageText` returns the `text` field and does not error

---

### Requirement: Guardrail factory uses defineRealtimeOutputGuardrail

The system SHALL define output guardrails using `defineRealtimeOutputGuardrail()` from `@openai/agents/realtime`, replacing the previous plain-object shape.

The previous `{ name, async execute({agentOutput}) → { tripwireTriggered, outputInfo } }` interface is no longer accepted by the SDK.

#### Scenario: Guardrail is accepted by RealtimeSession

- **WHEN** `createModerationGuardrail(companyName, profile)` is called
- **THEN** the returned object is a valid `RealtimeOutputGuardrailDefinition` accepted by `new RealtimeSession(..., { outputGuardrails: [guardrail] })`
- **THEN** the internal `runGuardrailClassifier` logic calling `/api/responses` is unchanged

#### Scenario: Guardrail trip is triggered on policy violation

- **WHEN** `runGuardrailClassifier` returns a category in `{ OFFENSIVE, VIOLENCE }` (or `OFF_BRAND` for company profile)
- **THEN** the guardrail returns a result that causes the SDK to fire `guardrail_tripped`
- **THEN** the `GuardrailChip` updates to reflect the violation category and rationale
