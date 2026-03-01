# SPEC003 — Default General-Purpose Agent

## Goal

Create a **default general-purpose agent scenario** that exposes the maximum set of available tools out of the box — comparable to ChatGPT or Claude in capability. The agent should be able to search the web, execute code, generate images, and search uploaded files, making it immediately useful without domain-specific customization.

This becomes the "batteries included" entry point for Hob — a single voice agent that can do most things a user would expect from a modern AI assistant.

---

## Background: SDK Tool Constraints

The OpenAI Agents SDK imposes a key architectural constraint:

| Context | Supported tool types |
| --- | --- |
| **Realtime session** (voice) | `FunctionTool`, `HostedMCPTool` only |
| **Responses API** (text model) | All tool types including hosted tools (`web_search`, `code_interpreter`, `file_search`, `image_generation`) |

This means the hosted tools **cannot** be attached directly to a `RealtimeAgent`. They must be accessed via a **supervisor delegation pattern**: the realtime agent calls a function tool that proxies the request to `/api/responses`, where the text model has access to the hosted tools.

This is the same pattern used by the existing `chatSupervisor` scenario, but generalized to support the full set of hosted tools.

---

## Architecture

```
User (voice)
  │
  ▼
RealtimeAgent ("assistant")
  │
  ├── Direct voice responses (simple questions, conversation)
  │
  └── FunctionTool: delegateToSupervisor
        │
        ▼
      /api/responses (text model: gpt-4.1)
        │
        ├── web_search        — real-time web queries
        ├── code_interpreter   — code execution, data analysis, math
        ├── file_search        — search uploaded documents (requires vector store)
        └── image_generation   — create images from descriptions
```

The realtime agent handles conversational voice directly. When a task requires tools (web search, code, etc.), it delegates to the supervisor which has the full hosted tool set.

---

## Scenario Definition

**Scenario name**: `default` (replaces the current default or becomes the new default)

**Agents**: Single agent — no multi-agent handoffs needed for the default scenario.

| Agent | Role |
| --- | --- |
| `assistant` | General-purpose voice agent with supervisor delegation |

---

## Agent: `assistant`

### Instructions

The agent should be a helpful, general-purpose AI assistant. Key behaviors:

- Answer simple questions directly from its own knowledge (no tool call needed)
- Delegate to the supervisor for anything requiring up-to-date information, computation, code execution, image creation, or document search
- Be concise — responses are spoken aloud, so avoid long lists or dense formatting
- When reporting supervisor results, paraphrase naturally for voice rather than reading raw output

### Tools

**Realtime tool** (runs client-side):

| Tool | Description |
| --- | --- |
| `delegateToSupervisor` | Sends the user's request to a text model with access to web search, code interpreter, file search, and image generation. Returns the result as text. |

The `delegateToSupervisor` tool follows the same pattern as `getNextResponseFromSupervisor` in the chatSupervisor scenario:

1. Collects recent conversation history from `details?.context?.history`
2. Sends it along with the user's request to `/api/responses`
3. The Responses API call includes the hosted tools: `web_search`, `code_interpreter`, and optionally `file_search` / `image_generation`
4. Iteratively handles tool calls (the supervisor may call multiple tools in sequence)
5. Returns the final text response

### Supervisor Configuration

The text model called via `/api/responses` should be configured with:

```ts
const supervisorTools = [
  { type: "web_search_preview" },
  { type: "code_interpreter" },
  // file_search requires a vector_store_id — include only when configured
  // { type: "file_search", vector_store_ids: [process.env.OPENAI_VECTOR_STORE_ID] },
  // image_generation is optional — results are text descriptions in voice mode
  // { type: "image_generation" },
];
```

**Tool availability**:

| Tool | Availability | Notes |
| --- | --- | --- |
| `web_search` | Always enabled | No additional configuration needed |
| `code_interpreter` | Always enabled | Runs in OpenAI's sandboxed environment |
| `file_search` | Conditional | Requires `OPENAI_VECTOR_STORE_ID` env var pointing to an existing vector store |
| `image_generation` | Conditional | Limited value in voice-only mode (no visual display yet); enable when avatar panel can show images |

### Supervisor Instructions

The supervisor prompt should be general-purpose:

- You are a helpful assistant with access to tools
- Use web search for current events, facts, prices, or anything that may have changed since your training
- Use code interpreter for math, data analysis, code execution, or anything computational
- Use file search when the user asks about uploaded documents (only when available)
- Be concise — your response will be spoken aloud by a voice agent
- Provide sources/citations when using web search results

---

## Environment Variables

New variables (all optional):

```env
# Vector store ID for file_search tool (optional)
OPENAI_VECTOR_STORE_ID=vs_...
```

No changes to existing variables. The agent uses the same provider resolution (`LLM_PROVIDER` / auto-detect) as all other routes.

---

## Files Changed

| File | Change |
| --- | --- |
| `src/app/agentConfigs/defaultAssistant/index.ts` | New: scenario definition with single `assistant` agent |
| `src/app/agentConfigs/defaultAssistant/supervisorTools.ts` | New: supervisor tool definitions and delegation logic |
| `src/app/agentConfigs/index.ts` | Update: add `defaultAssistant` to `allAgentSets`, potentially change `defaultAgentSetKey` |
| `src/app/App.tsx` | Update: add `defaultAssistant` to `sdkScenarioMap` and company-name mapping |
| `src/app/agentConfigs/avatarConfig.ts` | Update: add `assistant` to avatar configs |

---

## Open Questions / Risks

| # | Question | Impact |
| --- | --- | --- |
| 1 | Should `image_generation` be enabled given that Hob is voice-first with no image display in the conversation? | Could describe images verbally, or wait until the avatar panel supports image rendering |
| 2 | Should `file_search` require a pre-existing vector store, or should the agent be able to create one on-the-fly? | On-the-fly creation adds complexity; start with pre-configured vector store via env var |
| 3 | Should this replace `chatSupervisor` as the default scenario, or coexist alongside it? | Recommend replacing as default since this is a strict superset in capability |
| 4 | Does the `web_search` hosted tool work with Azure OpenAI, or is it direct-OpenAI only? | Must verify — may need to be disabled in Azure mode if unsupported |
| 5 | Should the supervisor model be configurable (e.g. `gpt-4.1` vs `o4-mini`) via env var? | `gpt-4.1` is a good default; could add `OPENAI_SUPERVISOR_MODEL` for flexibility |

---

## Out of Scope

- Multi-agent handoffs (this is a single-agent scenario)
- Custom domain tools (use `chatSupervisor` or `customerServiceRetail` for domain-specific setups)
- File upload UI (file_search assumes a pre-configured vector store)
- Image display in the conversation panel (voice-only for now)
- MCP server integration (could be a future enhancement)
