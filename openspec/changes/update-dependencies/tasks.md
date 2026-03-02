## 1. Update package.json and install

- [ ] 1.1 Bump `@openai/agents` to `^0.5.2` in `package.json`
- [ ] 1.2 Bump `next` to latest stable in `package.json`
- [ ] 1.3 Bump `openai` (base SDK) to latest stable in `package.json`
- [ ] 1.4 Bump `react` and `react-dom` to latest stable in `package.json`
- [ ] 1.5 Bump remaining deps (`uuid`, `zod`, `react-markdown`, `@radix-ui/react-icons`) to latest compatible versions
- [ ] 1.6 Run `npm install` and confirm lockfile updates without conflicts

## 2. Fix extractMessageText content type discriminants

- [ ] 2.1 In `useHandleSessionHistory.ts`, update `extractMessageText` to check `c.type === 'input_audio'` (was `'audio'`) for user audio transcript
- [ ] 2.2 Add check for `c.type === 'output_audio'` for assistant audio transcript
- [ ] 2.3 Verify `c.type === 'input_text'` path is unchanged (still returns `c.text`)

## 3. Fix agent_handoff handler

- [ ] 3.1 In `useRealtimeSession.ts`, update `handleAgentHandoff` signature to `(context, fromAgent, toAgent)`
- [ ] 3.2 Replace history-parsing logic (`item.context.history` + `"transfer_to_"` split) with `toAgent.name`
- [ ] 3.3 Verify `callbacks.onAgentHandoff(toAgent.name)` is called correctly

## 4. Fix agent_tool_start handler

- [ ] 4.1 In `useHandleSessionHistory.ts`, update `handleAgentToolStart` signature to `(context, agent, tool, details)`
- [ ] 4.2 Replace `extractFunctionCallByName(functionCall.name, details?.context?.history)` with `tool.name` and `details.toolCall.arguments`
- [ ] 4.3 Verify `addTranscriptBreadcrumb("function call: ${tool.name}", ...)` is called with correct args

## 5. Fix agent_tool_end handler

- [ ] 5.1 In `useHandleSessionHistory.ts`, update `handleAgentToolEnd` signature to `(context, agent, tool, result, details)`
- [ ] 5.2 Use `tool.name` for the function name (replacing the old `_functionCall.name` lookup)
- [ ] 5.3 Verify `addTranscriptBreadcrumb("function call result: ${tool.name}", maybeParseJson(result))` is called correctly

## 6. Fix guardrail_tripped handler

- [ ] 6.1 Inspect the `OutputGuardrailTripwireTriggered` type in vendor source (`agents-core`) to find exact path to `moderationCategory` and `moderationRationale` in the error object
- [ ] 6.2 In `useHandleSessionHistory.ts`, update `handleGuardrailTripped` signature to `(context, agent, error, details)`
- [ ] 6.3 Replace history-scan workaround with `details.itemId` as the target item ID
- [ ] 6.4 Update moderation extraction to use the correct field path from the new error object (replacing `extractModeration()` if the path has changed)
- [ ] 6.5 Verify `updateTranscriptItem(details.itemId, { guardrailResult: { status, category, rationale } })` is called

## 7. Fix history_updated handler

- [ ] 7.1 In `useHandleSessionHistory.ts`, update `handleHistoryUpdated` signature to `(history: RealtimeItem[])`
- [ ] 7.2 Update handler to iterate the full history array and only call `updateTranscriptMessage` for items whose `itemId` already exists in `transcriptItems` (reconcile, do not create)
- [ ] 7.3 Verify `status: DONE` items are not overwritten by stale history content

## 8. Rewrite guardrail factory

- [ ] 8.1 In `guardrails.ts`, import `defineRealtimeOutputGuardrail` from `@openai/agents/realtime` (reference vendor `guardrail.ts` for usage)
- [ ] 8.2 Rewrite `createModerationGuardrail` to use `defineRealtimeOutputGuardrail()`, mapping the existing `runGuardrailClassifier` result to the new `OutputGuardrailResult` shape
- [ ] 8.3 Verify the returned object is accepted by `new RealtimeSession(..., { outputGuardrails: [guardrail] })` without TypeScript errors
- [ ] 8.4 Verify `isTripwireTriggered` logic is preserved (OFFENSIVE, VIOLENCE → always; OFF_BRAND → company profile only)

## 9. Fix API routes for updated openai base SDK

- [ ] 9.1 In `api/session/route.ts`, verify `fetch` call to OpenAI session endpoint is compatible with any changed base SDK types
- [ ] 9.2 In `api/responses/route.ts`, verify `openai.responses.create()` and `openai.responses.parse()` signatures are unchanged; fix if needed

## 10. Build verification and smoke test

- [ ] 10.1 Run `npm run build` — confirm zero TypeScript errors and zero build errors
- [ ] 10.2 Run `npm run dev` and connect a session; verify user speech transcribes and displays on the right
- [ ] 10.3 Verify AI response streams and displays on the left; verify interruption works
- [ ] 10.4 Trigger a tool call (e.g., ask a web search question); verify breadcrumbs appear and AI synthesizes a response
- [ ] 10.5 Verify agent handoff works (using `simpleHandoff` scenario); verify breadcrumb is recorded with correct agent name
- [ ] 10.6 Verify guardrail trip is reflected in the `GuardrailChip` on the offending message
