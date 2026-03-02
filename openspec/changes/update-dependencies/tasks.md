## 1. Update package.json and install

- [x] 1.1 Bump `@openai/agents` to `^0.5.2` in `package.json`
- [x] 1.2 Bump `next` to latest stable in `package.json`
- [x] 1.3 Bump `openai` (base SDK) to latest stable in `package.json`
- [x] 1.4 Bump `react` and `react-dom` to latest stable in `package.json`
- [x] 1.5 Bump remaining deps (`uuid`, `zod`, `react-markdown`, `@radix-ui/react-icons`) to latest compatible versions
- [x] 1.6 Run `npm install` and confirm lockfile updates without conflicts

## 2. Fix extractMessageText content type discriminants

- [x] 2.1 In `useHandleSessionHistory.ts`, update `extractMessageText` to check `c.type === 'input_audio'` (was `'audio'`) for user audio transcript
- [x] 2.2 Add check for `c.type === 'output_audio'` for assistant audio transcript
- [x] 2.3 Verify `c.type === 'input_text'` path is unchanged (still returns `c.text`)

## 3. Fix agent_handoff handler

- [x] 3.1 In `useRealtimeSession.ts`, update `handleAgentHandoff` signature to `(context, fromAgent, toAgent)`
- [x] 3.2 Replace history-parsing logic (`item.context.history` + `"transfer_to_"` split) with `toAgent.name`
- [x] 3.3 Verify `callbacks.onAgentHandoff(toAgent.name)` is called correctly

## 4. Fix agent_tool_start handler

- [x] 4.1 In `useHandleSessionHistory.ts`, update `handleAgentToolStart` signature to `(context, agent, tool, details)`
- [x] 4.2 Replace `extractFunctionCallByName(functionCall.name, details?.context?.history)` with `tool.name` and `details.toolCall.arguments`
- [x] 4.3 Verify `addTranscriptBreadcrumb("function call: ${tool.name}", ...)` is called with correct args

## 5. Fix agent_tool_end handler

- [x] 5.1 In `useHandleSessionHistory.ts`, update `handleAgentToolEnd` signature to `(context, agent, tool, result, details)`
- [x] 5.2 Use `tool.name` for the function name (replacing the old `_functionCall.name` lookup)
- [x] 5.3 Verify `addTranscriptBreadcrumb("function call result: ${tool.name}", maybeParseJson(result))` is called correctly

## 6. Fix guardrail_tripped handler

- [x] 6.1 Inspect the `OutputGuardrailTripwireTriggered` type in vendor source (`agents-core`) to find exact path to `moderationCategory` and `moderationRationale` in the error object
- [x] 6.2 In `useHandleSessionHistory.ts`, update `handleGuardrailTripped` signature to `(context, agent, error, details)`
- [x] 6.3 Replace history-scan workaround with `details.itemId` as the target item ID
- [x] 6.4 Update moderation extraction to use the correct field path from the new error object (replacing `extractModeration()` if the path has changed)
- [x] 6.5 Verify `updateTranscriptItem(details.itemId, { guardrailResult: { status, category, rationale } })` is called

## 7. Fix history_updated handler

- [x] 7.1 In `useHandleSessionHistory.ts`, update `handleHistoryUpdated` signature to `(history: RealtimeItem[])`
- [x] 7.2 Update handler to iterate the full history array and only call `updateTranscriptMessage` for items whose `itemId` already exists in `transcriptItems` (reconcile, do not create)
- [x] 7.3 Verify `status: DONE` items are not overwritten by stale history content

## 8. Rewrite guardrail factory

- [x] 8.1 In `guardrails.ts`, use the supported public realtime guardrail API from `@openai/agents/realtime` (`RealtimeOutputGuardrail`) compatible with the installed SDK
- [x] 8.2 Rewrite `createModerationGuardrail` to return an SDK-accepted realtime output guardrail object while preserving `tripwireTriggered` and `outputInfo` mapping
- [x] 8.3 Verify the returned object is accepted by `new RealtimeSession(..., { outputGuardrails: [guardrail] })` without TypeScript errors
- [x] 8.4 Verify `isTripwireTriggered` logic is preserved (OFFENSIVE, VIOLENCE → always; OFF_BRAND → company profile only)

## 9. Fix API routes for updated openai base SDK

- [x] 9.1 In `api/session/route.ts`, verify `fetch` call to OpenAI session endpoint is compatible with any changed base SDK types
- [x] 9.2 In `api/responses/route.ts`, verify `openai.responses.create()` and `openai.responses.parse()` signatures are unchanged; fix if needed

## 10. Build verification and smoke test

- [x] 10.1 Run build verification in this environment (use `npm run build -- --webpack` when Turbopack is sandbox-blocked) and confirm zero TypeScript/build errors
- [ ] 10.2 Run `npm run dev` and connect a session; verify user speech transcribes and displays on the right
- [ ] 10.3 Verify AI response streams and displays on the left; verify interruption works
- [ ] 10.4 Trigger a tool call (e.g., ask a web search question); verify breadcrumbs appear and AI synthesizes a response
- [ ] 10.5 Verify agent handoff works (using `simpleHandoff` scenario); verify breadcrumb is recorded with correct agent name
- [ ] 10.6 Verify guardrail trip is reflected in the `GuardrailChip` on the offending message
