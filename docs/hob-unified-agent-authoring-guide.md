# Hob Unified Agent Authoring Guide

This guide shows how to build a new agent scenario that combines all major capabilities already present in Hob:

- Realtime voice interaction (`simpleHandoff`, `chatSupervisor`, `customerServiceRetail`)
- Multi-agent handoffs (`simpleHandoff`, `customerServiceRetail`)
- Tool-calling with local execution (`customerServiceRetail`)
- Supervisor reasoning loop via Responses API (`chatSupervisor`)
- Validation layers (decision validator + output guardrail)

The intent is one coherent pattern for production-style agents, based on the current code in `src/app`.

## 1. Core Terms: Agent vs Agent Scenario

Use these terms consistently when designing new configs:

| Term | Meaning in Hob | Shape |
| --- | --- | --- |
| **Agent** | One specialized runtime role with its own prompt, tools, voice, and handoff options | `new RealtimeAgent({...})` |
| **Agent scenario** | A named group of agents used as one selectable session configuration | `RealtimeAgent[]` |

Concrete examples from this repo:

- **Agents**: `chatAgent`, `authenticationAgent`, `returnsAgent`, `salesAgent`, `simulatedHumanAgent`.
- **Scenarios**: `chatSupervisorScenario`, `customerServiceRetailScenario`, `simpleHandoffScenario`.

Practical implication:

- You author and test **agents** individually.
- You deploy and select **scenarios** in the app (`?agentConfig=<scenarioKey>`).

## 2. Capability Map From Current Demos

| Capability | Existing reference |
| --- | --- |
| Realtime root agent + handoff graph | `src/app/agentConfigs/simpleHandoff.ts`, `src/app/agentConfigs/customerServiceRetail/index.ts` |
| Domain tools with JSON schema params | `src/app/agentConfigs/customerServiceRetail/*.ts` |
| Supervisor tool delegating to Responses API | `src/app/agentConfigs/chatSupervisor/supervisorAgent.ts` |
| Validation agent for high-stakes decisions | `checkEligibilityAndPossiblyInitiateReturn` in `returns.ts` |
| Output moderation guardrail | `src/app/agentConfigs/guardrails.ts` + `outputGuardrails` wiring in `src/app/App.tsx` |
| Session/event/transcript integration | `src/app/hooks/useRealtimeSession.ts`, `src/app/hooks/useHandleSessionHistory.ts` |

## 3. Unified Target Architecture

Use a layered design:

1. Realtime frontline agents for low-latency voice UX.
2. Deterministic tools for business actions and data retrieval.
3. A supervisor tool for complex reasoning/planning.
4. A validation agent/tool for policy-critical decisions.
5. Output guardrails for moderation and brand safety.

At runtime this is:

- `RealtimeAgent` receives user speech.
- Agent either responds directly, calls a local tool, or delegates to supervisor.
- For sensitive actions, a validator model/tool confirms eligibility before action.
- Final assistant output is checked by guardrails.
- Handoff transfers control to specialized agents when needed.

## 4. File/Code Pattern To Follow

Create a new folder, e.g.:

`src/app/agentConfigs/unifiedSupport/`

Recommended files:

- `index.ts`: scenario export, handoff wiring, company name
- `intake.ts`: root/frontline agent
- `specialistReturns.ts`: return flow + validator tool
- `specialistSales.ts`: sales tools
- `humanEscalation.ts`: escalation endpoint agent
- `supervisor.ts`: Responses API delegation tool (pattern from chat supervisor)

## 5. Build Steps

### Step 1: Define specialist agents and tools

Use `new RealtimeAgent({...})` and `tool({...})` exactly like existing configs.

`RealtimeAgent` constructor accepts:

| Option | Type | Notes |
| --- | --- | --- |
| `name` | `string` | **Required** — unique identifier for the agent |
| `instructions` | `string \| ((ctx) => string)` | System prompt |
| `handoffs` | `(RealtimeAgent \| Handoff)[]` | Agents this agent can transfer to |
| `tools` | `Tool[]` | Tools available to this agent |
| `voice` | `string` | Voice for this agent (e.g. `'alloy'`, `'shimmer'`) |

**SDK constraint**: `RealtimeAgent` does **not** accept `model`, `modelSettings`, `outputGuardrails`, or `inputGuardrails`. All agents in a session share the same model (set on `RealtimeSession`) and the same output guardrails (set via `RealtimeSessionOptions.outputGuardrails`).

Rules from current codebase:

- Keep tool schemas strict (`required`, `additionalProperties: false`).
- Keep tool logic deterministic where possible.
- For tool observability, use `details?.context` + `addTranscriptBreadcrumb` (see supervisor pattern).
- Set `voice` per agent if different agents should sound different (e.g. a human-escalation agent could use a distinct voice).

### Step 2: Add a validation tool/agent for high-risk actions

Pattern: the returns agent already does this by calling `/api/responses` with `model: "o4-mini"` in `checkEligibilityAndPossiblyInitiateReturn`.

Use this same approach for:

- refunds
- account changes
- irreversible operations
- policy exceptions

Implementation pattern:

1. Gather recent conversation context from `details?.context?.history`.
2. Send concise policy + context prompt to `/api/responses`.
3. Return structured verdict (`eligible`, `ineligible`, `need_more_information`).
4. Only perform final action when verdict is positive.

### Step 3: Add a supervisor delegation tool for complex reasoning

Use the `getNextResponseFromSupervisor` pattern in:

- `src/app/agentConfigs/chatSupervisor/supervisorAgent.ts`

Key behaviors to preserve:

- Include recent conversation history in the request body.
- Allow iterative function-call loops until final text is produced.
- Force `parallel_tool_calls: false` in the Responses API request body if tool order matters. Note: this is a `ModelSettings` property for text-model calls only — it cannot be set on `RealtimeAgent` (which omits `modelSettings`).
- Return one final message that the realtime agent can speak verbatim.

### Step 4: Compose handoffs in one place

Follow `customerServiceRetail/index.ts`:

- Define agents first with `handoffs: []`.
- Wire graph centrally in `index.ts`.
- Export one ordered `RealtimeAgent[]` scenario where element 0 is default root.

### Step 5: Register the new scenario

Update:

- `src/app/agentConfigs/index.ts` (`allAgentSets`, optional default key)
- `src/app/App.tsx` (`sdkScenarioMap`)
- `src/app/App.tsx` company-name mapping used for guardrails

## 6. Guardrails and Validation in the Unified Model

There are two distinct safety layers and both should be kept:

1. Decision validation before action:
- Implemented as a tool that asks a stronger model to judge eligibility/policy.
- Example in `returns.ts` (`checkEligibilityAndPossiblyInitiateReturn`).

2. Output moderation after generation:
- Implemented by `createModerationGuardrail(companyName)` in `guardrails.ts`.
- Passed to session as `outputGuardrails` in `App.tsx`.
- Processed in history hook via `guardrail_tripped` event.

**SDK constraint**: Output guardrails are set at the **session level** (`RealtimeSessionOptions.outputGuardrails`), not per agent. All agents in a session share the same guardrails. The guardrail interface requires a `name` and a `run()` function returning an `OutputGuardrailResult`. An optional `debounceTextLength` setting (default 100) controls how much text accumulates before the guardrail is invoked.

These layers solve different problems:

- Validation agent: "Should we do this action?"
- Guardrail: "Is this response safe/on-brand to show?"

## 7. Minimal Scenario Skeleton

```ts
// src/app/agentConfigs/unifiedSupport/index.ts
import { intakeAgent } from './intake';
import { returnsAgent } from './specialistReturns';
import { salesAgent } from './specialistSales';
import { humanAgent } from './humanEscalation';

(intakeAgent.handoffs as any).push(returnsAgent, salesAgent, humanAgent);
(returnsAgent.handoffs as any).push(intakeAgent, salesAgent, humanAgent);
(salesAgent.handoffs as any).push(intakeAgent, returnsAgent, humanAgent);
(humanAgent.handoffs as any).push(intakeAgent, returnsAgent, salesAgent);

export const unifiedSupportScenario = [intakeAgent, returnsAgent, salesAgent, humanAgent];
export const unifiedSupportCompanyName = 'YourCompany';
```

## 8. OpenAI Agents SDK Source Reference

The full source code of the OpenAI Agents SDK (JavaScript/TypeScript) is available locally as a git submodule at `vendor/openai-agents-js`. This is the same SDK that provides `@openai/agents` and `@openai/agents/realtime` used throughout Hob.

When authoring agents, consult this source to determine:

- Available options for `RealtimeAgent`, `RealtimeSession`, and `OpenAIRealtimeWebRTC` constructors
- Supported parameters for `session.connect()` (e.g. `apiKey`, `url`)
- Tool definition schemas and execution interfaces
- Handoff mechanics and event types
- Guardrail interfaces and how `outputGuardrails` are evaluated

Key entry points in the SDK source:

| What | Path in `vendor/openai-agents-js` |
| --- | --- |
| Main re-export (`@openai/agents`) | `packages/agents/src/` |
| Realtime agents (`@openai/agents/realtime`) | `packages/agents-realtime/src/` |
| Core agent framework | `packages/agents-core/src/` |
| OpenAI provider | `packages/agents-openai/src/` |

### Key SDK types for Hob development

**`RealtimeSessionOptions`** (set when constructing `RealtimeSession`):

| Option | Type | Notes |
| --- | --- | --- |
| `transport` | `'webrtc' \| 'websocket' \| RealtimeTransportLayer` | Hob uses `OpenAIRealtimeWebRTC` |
| `model` | `string` | Shared across all agents in the session |
| `outputGuardrails` | `RealtimeOutputGuardrail[]` | Session-level, not per-agent |
| `outputGuardrailSettings` | `{ debounceTextLength: number }` | Default: 100 chars |
| `config` | `Partial<RealtimeSessionConfig>` | Input audio transcription, etc. |
| `context` | `TContext` | Shared context passed to tools |
| `historyStoreAudio` | `boolean` | Whether to store audio in history |
| `tracingDisabled` | `boolean` | Disable tracing |

**`session.connect()` options**:

| Option | Type | Notes |
| --- | --- | --- |
| `apiKey` | `string \| (() => string \| Promise<string>)` | **Required** |
| `url` | `string` | Custom endpoint (used for Azure WebRTC) |
| `model` | `string` | Override model at connect time |
| `callId` | `string` | For SIP transport |

**`OpenAIRealtimeWebRTC` constructor options**:

| Option | Type | Notes |
| --- | --- | --- |
| `audioElement` | `HTMLAudioElement` | For playback |
| `mediaStream` | `MediaStream` | Custom input stream |
| `baseUrl` | `string` | Custom base URL |
| `changePeerConnection` | `(pc) => pc` | Modify RTCPeerConnection (used for codec selection) |

**RealtimeSession events** (subscribe via `session.on(event, handler)`):

| Event | Payload | When |
| --- | --- | --- |
| `agent_start` | context, agent | Agent begins processing |
| `agent_end` | context, agent, output | Agent finishes |
| `agent_handoff` | context, fromAgent, toAgent | Control transfers |
| `agent_tool_start` | context, agent, tool, details | Tool invocation begins |
| `agent_tool_end` | context, agent, tool, result, details | Tool invocation completes |
| `transport_event` | event | Raw transport-level event |
| `audio_start` | context, agent | Audio generation begins |
| `audio_stopped` | context, agent | Audio generation stops |
| `audio_interrupted` | context, agent | User interrupted audio |
| `guardrail_tripped` | context, agent, error, details | Output guardrail triggered |
| `history_updated` | history | Conversation history changed |
| `history_added` | item | New item added to history |
| `error` | error | Session error |
| `tool_approval_requested` | context, agent, request | Tool needs user approval |

## 9. Runtime Facts To Keep In Mind

- Realtime session key is minted in `src/app/api/session/route.ts`. In Azure mode, the route also returns a `realtimeUrl` for the WebRTC endpoint.
- Text-model reasoning and structured parsing run through `src/app/api/responses/route.ts`. In Azure mode, `AzureOpenAI` is used and `body.model` is rewritten to the deployment name.
- Provider selection uses `resolveProvider()` from `src/app/lib/resolveProvider.ts` — see `LLM_PROVIDER` env var or auto-detection via `OPENAI_API_KEY` / `AZURE_OPENAI_ENDPOINT`.
- Realtime tool execution for SDK agents happens in the client runtime (tool `execute` functions).
- Session wiring, guardrails, and handoff UI sync happen in `src/app/App.tsx` and `src/app/hooks/useRealtimeSession.ts`.
- All agents in a `RealtimeSession` share the same model, guardrails, and context. Per-agent differentiation is limited to `name`, `instructions`, `tools`, `handoffs`, and `voice`.

## 10. Practical Quality Checklist

Before shipping a new unified agent scenario:

1. Handoff graph tested in both directions where intended.
2. Every sensitive tool path gated by validator verdict.
3. Supervisor tool handles missing required info by asking follow-up questions.
4. Guardrail events appear correctly in transcript UI.
5. Tool call arguments/results are visible as breadcrumbs for debugging.
6. Scenario is selectable via `?agentConfig=<yourKey>`.

## 11. Suggested Next Implementation

If you want this fully wired immediately, implement `unifiedSupport` as a fourth scenario under `src/app/agentConfigs/` using the structure above, then register it in `allAgentSets` and `sdkScenarioMap`.
