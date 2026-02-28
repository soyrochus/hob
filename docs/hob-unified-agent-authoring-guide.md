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
| **Agent** | One specialized runtime role with its own prompt, tools, and handoff options | `new RealtimeAgent({...})` |
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

Rules from current codebase:

- Keep tool schemas strict (`required`, `additionalProperties: false`).
- Keep tool logic deterministic where possible.
- For tool observability, use `details?.context` + `addTranscriptBreadcrumb` (see supervisor pattern).

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
- Force `parallel_tool_calls: false` if tool order matters.
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

## 8. Runtime Facts To Keep In Mind

- Realtime session key is minted in `src/app/api/session/route.ts`.
- Text-model reasoning and structured parsing run through `src/app/api/responses/route.ts`.
- Realtime tool execution for SDK agents happens in the client runtime (tool `execute` functions).
- Session wiring, guardrails, and handoff UI sync happen in `src/app/App.tsx` and `src/app/hooks/useRealtimeSession.ts`.

## 9. Practical Quality Checklist

Before shipping a new unified agent scenario:

1. Handoff graph tested in both directions where intended.
2. Every sensitive tool path gated by validator verdict.
3. Supervisor tool handles missing required info by asking follow-up questions.
4. Guardrail events appear correctly in transcript UI.
5. Tool call arguments/results are visible as breadcrumbs for debugging.
6. Scenario is selectable via `?agentConfig=<yourKey>`.

## 10. Suggested Next Implementation

If you want this fully wired immediately, implement `unifiedSupport` as a fourth scenario under `src/app/agentConfigs/` using the structure above, then register it in `allAgentSets` and `sdkScenarioMap`.
