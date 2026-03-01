## Context

Hob currently emphasizes demo-specific scenarios. The new change introduces a single "defaultAssistant" scenario that behaves like a general-purpose assistant and can immediately handle broad user requests.

The main technical constraint is that realtime agent tools in this app are limited at runtime, while OpenAI hosted tools (`web_search`, `code_interpreter`, `file_search`) are available through the Responses API. The design therefore needs a delegation path from the realtime voice loop to a text-based supervisor call via `/api/responses`.

## Goals / Non-Goals

**Goals:**
- Provide a default general-purpose voice assistant scenario with no domain setup required.
- Reuse the existing supervisor pattern (`getNextResponseFromSupervisor`) so tool execution happens through Responses API hosted tools.
- Keep existing demo scenarios unchanged and still selectable.
- Support optional document search through `file_search` when configured.

**Non-Goals:**
- Building a new backend orchestration service outside the existing `/api/responses` path.
- Replacing existing scenario-specific agents.
- Adding new npm dependencies or custom external tool infrastructure.
- Creating a runtime UI for per-tool toggles in this change.

## Decisions

### 1. Add a dedicated `defaultAssistant` scenario with one realtime `assistant` agent

**Decision:** Create `src/app/agentConfigs/defaultAssistant/index.ts` with a single root agent focused on broad conversational behavior and delegation.

**Rationale:** A standalone scenario keeps the change isolated and easy to reason about. One-agent topology avoids unnecessary handoff complexity while still supporting advanced tasks through supervisor calls.

**Alternatives considered:**
- Reusing one of the existing demo agents and broadening its instructions. Rejected because it couples generic behavior to domain-specific prompts and tools.
- Multi-agent default setup (assistant + specialist sub-agents). Rejected for initial version due to higher prompt/tool routing complexity.

### 2. Use supervisor delegation for hosted tools through `/api/responses`

**Decision:** Implement `src/app/agentConfigs/defaultAssistant/supervisorTools.ts` using the same supervisor request/response flow as `chatSupervisor`, but with hosted tools payload (`web_search`, `code_interpreter`, and optional `file_search`).

**Rationale:** This aligns with current architecture and avoids introducing unsupported realtime tool types. It also centralizes hosted tool usage in one known API surface already present in the app.

**Alternatives considered:**
- Calling hosted tools directly from realtime session tools. Rejected due to runtime/tooling constraints in current realtime flow.
- Creating separate server endpoints per hosted tool. Rejected because `/api/responses` already supports generic payload forwarding.

### 3. Register scenario and avatar through existing indexes only

**Decision:** Wire `defaultAssistant` into `allAgentSets`, `sdkScenarioMap`, and avatar configuration files, optionally setting it as `defaultAgentSetKey`.

**Rationale:** The app already routes scenario selection through these registries. Reusing that mechanism minimizes risk and keeps UI behavior consistent.

**Alternatives considered:**
- Special-case scenario selection in `App.tsx`. Rejected because it adds bespoke logic and diverges from established configuration patterns.

### 4. Keep `/api/responses` contract unchanged

**Decision:** Do not add a new API contract; send hosted tools in existing request body and consume standard response content.

**Rationale:** Existing route intentionally proxies Responses API requests. Keeping the contract stable reduces regression risk for other scenarios.

**Alternatives considered:**
- Extending `/api/responses` with scenario-specific behavior flags. Rejected as unnecessary coupling and added complexity.

## Risks / Trade-offs

- [Tool latency variability] Hosted tools (especially web/code) can be slower than plain generation. → Mitigation: keep supervisor call pattern asynchronous and maintain user-facing continuity in voice updates.
- [Instruction over-breadth] A single "general-purpose" prompt may behave inconsistently across domains. → Mitigation: include explicit delegation criteria and conservative fallback behavior in agent instructions.
- [Optional `file_search` misconfiguration] Missing vector store setup could cause degraded behavior. → Mitigation: make `file_search` optional; include graceful fallback when not configured.
- [Default scenario change surprise] Switching `defaultAgentSetKey` may alter first-run behavior for existing users. → Mitigation: treat default switch as optional and document it clearly.

## Migration Plan

1. Add new `defaultAssistant` config files.
2. Register scenario in agent set exports and SDK scenario map.
3. Add avatar config entry for the new assistant.
4. Decide whether to set `defaultAgentSetKey` to `defaultAssistant`.
5. Validate app startup and scenario selection.
6. Validate supervisor delegation and hosted tool behavior via `/api/responses`.
7. Rollback plan: revert registry wiring (`allAgentSets`, `defaultAgentSetKey`, `sdkScenarioMap`, avatar config) to remove the scenario without touching existing ones.

## Open Questions

1. Should `defaultAssistant` become the default immediately or remain opt-in initially?
2. What exact enablement condition should gate `file_search` (env var, static config, or both)?
3. What guardrails/instruction constraints are needed to avoid overusing expensive hosted tools?
