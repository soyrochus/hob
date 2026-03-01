## 1. Default Assistant Supervisor Tooling

- [x] 1.1 Create `src/app/agentConfigs/defaultAssistant/supervisorTools.ts` with hosted-tool declarations for `web_search` and `code_interpreter`
- [x] 1.2 Add optional `file_search` inclusion logic (for example via `NEXT_PUBLIC_OPENAI_VECTOR_STORE_ID`) so delegation works with or without document search configuration
- [x] 1.3 Implement `getNextResponseFromSupervisor` in the new module to call `/api/responses`, process tool-call turns, and return `nextResponse` with safe error fallback

## 2. Default Assistant Agent Scenario

- [x] 2.1 Create `src/app/agentConfigs/defaultAssistant/index.ts` with a single realtime `assistant` agent configured for general-purpose voice conversation
- [x] 2.2 Wire the assistant to use `getNextResponseFromSupervisor` for hosted-tool-required work and export `defaultAssistantScenario`

## 3. Scenario Registration

- [x] 3.1 Register `defaultAssistant` in `src/app/agentConfigs/index.ts` under `allAgentSets`
- [x] 3.2 Decide and apply `defaultAgentSetKey` behavior for this change (switch to `defaultAssistant` or keep current default)
- [x] 3.3 Update `src/app/App.tsx` imports and `sdkScenarioMap` so `agentConfig=defaultAssistant` resolves and connects correctly

## 4. Avatar and Guardrail Wiring

- [x] 4.1 Add an avatar config entry in `src/app/agentConfigs/avatarConfig.ts` for the new assistant agent name
- [x] 4.2 Update `App.tsx` scenario-to-company guardrail mapping so `defaultAssistant` is handled without changing existing scenario behavior

## 5. Optional File Search Configuration

- [x] 5.1 Document the optional file-search configuration variable in `.env.sample` for `defaultAssistant` delegation
- [x] 5.2 Verify the assistant continues working when file-search configuration is absent (web search and code interpreter still available)

## 6. Validation

- [x] 6.1 Run `npm run lint` and fix any issues introduced by the new scenario integration
- [x] 6.2 Manually verify startup and scenario selection for `defaultAssistant` and existing scenarios
