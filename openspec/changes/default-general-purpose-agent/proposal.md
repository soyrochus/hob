## Why

Hob currently ships with domain-specific demo scenarios (telecom customer service, retail returns, simple handoff) but no general-purpose agent. New users must understand the demo scenarios before they can do anything useful. A "batteries included" default agent — comparable to ChatGPT or Claude in capability — gives Hob immediate utility out of the box: web search, code execution, document search, and general conversation, all via voice.

## What Changes

- Add a new `defaultAssistant` scenario with a single general-purpose `assistant` agent
- The agent delegates to a supervisor text model (via `/api/responses`) for tasks requiring hosted tools: `web_search`, `code_interpreter`, and optionally `file_search`
- The supervisor delegation follows the existing `getNextResponseFromSupervisor` pattern from `chatSupervisor`, generalized to use OpenAI's hosted tools instead of domain-specific function tools
- Register the new scenario in `allAgentSets`, `sdkScenarioMap`, and avatar configs
- Optionally change `defaultAgentSetKey` to point to the new scenario

## Capabilities

### New Capabilities

- `default-assistant-agent`: A general-purpose voice agent with supervisor delegation providing web search, code execution, and document search out of the box

### Modified Capabilities

## Impact

- **New files**: `src/app/agentConfigs/defaultAssistant/index.ts`, `src/app/agentConfigs/defaultAssistant/supervisorTools.ts`
- **Modified files**: `src/app/agentConfigs/index.ts`, `src/app/App.tsx`, `src/app/agentConfigs/avatarConfig.ts`
- **Dependencies**: No new packages — uses existing `openai` SDK hosted tool types
- **APIs**: `/api/responses` is reused as-is; hosted tools are specified in the request body sent to the Responses API
- **Constraint**: Realtime sessions only support `FunctionTool` and `HostedMCPTool`; hosted tools (`web_search`, `code_interpreter`, `file_search`) must be accessed via the Responses API through a supervisor delegation tool
