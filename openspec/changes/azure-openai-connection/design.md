## Context

Hob connects to OpenAI via three independent call sites, all hardcoded to `api.openai.com`:

1. **Session route** (`/api/session`) — server-side `fetch` to mint an ephemeral Realtime session key
2. **Responses route** (`/api/responses`) — server-side `new OpenAI({ apiKey })` for supervisor/guardrail calls
3. **Realtime hook** (`useRealtimeSession`) — browser-side `session.connect({ apiKey })` for WebRTC

Azure OpenAI exposes the same capabilities behind different URLs, auth headers, and deployment-name-based routing. The switch must be configuration-only (env vars), with zero UI changes and full backward compatibility when Azure vars are absent.

## Goals / Non-Goals

**Goals:**
- Support Azure OpenAI as an alternative backend via `AZURE_OPENAI_*` environment variables
- Preserve the existing direct-OpenAI path unchanged when Azure vars are absent
- Keep the provider decision server-side — the browser should not know which provider is in use
- No new npm dependencies

**Non-Goals:**
- Runtime provider switching or UI-based provider selection
- Supporting both providers simultaneously (one or the other per deployment)
- Azure AD / managed identity auth (API key auth only)
- Azure Government or sovereign cloud endpoints

## Decisions

### 1. Three-tier provider detection: explicit → auto-detect → fail

**Decision**: Use a three-tier resolution strategy:

1. **Explicit**: If `LLM_PROVIDER` is set to `openai` or `azure`, use that provider directly. This enables rapid switching between providers without touching credential variables.
2. **Auto-detect**: If `LLM_PROVIDER` is unset, check for credentials in order — `OPENAI_API_KEY` first, then `AZURE_OPENAI_ENDPOINT`. The first one found determines the provider.
3. **Fail**: If no provider can be resolved (no `LLM_PROVIDER` and no credentials found), throw a runtime exception with a clear error message listing the expected variables.

```ts
function resolveProvider(): "openai" | "azure" {
  const explicit = process.env.LLM_PROVIDER;
  if (explicit === "openai" || explicit === "azure") return explicit;
  if (explicit) throw new Error(`Invalid LLM_PROVIDER "${explicit}". Must be "openai" or "azure".`);
  if (process.env.OPENAI_API_KEY) return "openai";
  if (process.env.AZURE_OPENAI_ENDPOINT) return "azure";
  throw new Error("No LLM provider configured. Set LLM_PROVIDER or provide OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT.");
}
```

**Rationale**: `LLM_PROVIDER` gives operators a single knob to flip when both sets of credentials are present (e.g. testing Azure against a staging environment while production uses direct OpenAI). Auto-detection preserves backward compatibility — existing deployments with only `OPENAI_API_KEY` continue working without adding `LLM_PROVIDER`. The fail-hard behavior prevents silent misconfiguration.

**Alternative considered**: Detection based solely on `AZURE_OPENAI_ENDPOINT` presence. Rejected because it doesn't support rapid switching when both credential sets are configured side by side.

### 2. Server-side URL injection for WebRTC endpoint

**Decision**: The `/api/session` route returns an optional `realtimeUrl` field. The browser passes it through to `session.connect({ url })` without interpreting it.

**Rationale**: This keeps all Azure-specific logic server-side. The hook and App.tsx don't need to import Azure config or build URLs — they just forward what the server tells them. If `realtimeUrl` is undefined (direct-OpenAI path), the SDK uses its default endpoint.

**Alternative considered**: Having the browser read a `/api/config` endpoint to learn the provider, then construct URLs client-side. Rejected because it leaks provider details to the client and adds a round-trip.

### 3. Use `AzureOpenAI` from the `openai` package for Responses API

**Decision**: Import `AzureOpenAI` from `openai` and use a `buildClient()` factory that returns either `OpenAI` or `AzureOpenAI` based on env vars.

**Rationale**: `AzureOpenAI` extends `OpenAI` and exposes the same `responses.create/parse` surface. The existing `structuredResponse` and `textResponse` helpers accept `OpenAI` and work identically with either client. No code changes needed downstream of the client construction.

**Alternative considered**: Manually constructing Azure REST calls with `fetch`. Rejected because the SDK already handles API version injection, auth headers, and deployment-name routing.

### 4. Model name rewriting in the responses proxy

**Decision**: When in Azure mode, replace `body.model` with the deployment name from `AZURE_OPENAI_RESPONSES_DEPLOYMENT` before forwarding to the SDK.

**Rationale**: Azure OpenAI routes by deployment name, not model name. The agent configs use model names (e.g. `gpt-4.1`) which don't resolve on Azure. Server-side rewriting keeps agent configs provider-agnostic.

### 5. `getEphemeralKey` return type change

**Decision**: Change `ConnectOptions.getEphemeralKey` from `() => Promise<string>` to `() => Promise<{ key: string; realtimeUrl?: string }>`.

**Rationale**: This is the minimal contract change needed to thread the WebRTC URL from server to transport. The optional `realtimeUrl` field means the direct-OpenAI path needs no changes beyond returning `{ key: ek }`.

## Risks / Trade-offs

- **Azure Realtime API availability** — Not all Azure OpenAI tiers/regions support the Realtime API. → Mitigation: document as a prerequisite; the session route will return a clear error if the Azure endpoint rejects the request.

- **Azure Responses API availability** — `openai.responses` requires API version `2025-04-01-preview` or later and may not be enabled on all Azure resources. → Mitigation: if unavailable, supervisor and guardrail features won't work but voice realtime still will. Document this as a known limitation.

- **SDK `connect({ url })` support** — The `@openai/agents` `OpenAIRealtimeWebRTC` transport must accept a custom `url` in `connect()`. → Mitigation: verify against the installed SDK version before implementing Change 3. If unsupported, may need to subclass or patch the transport.

- **Deployment name mismatch** — Azure deployment names may not match model names used in agent configs. → Mitigation: explicit env vars per deployment (`AZURE_OPENAI_REALTIME_DEPLOYMENT`, `AZURE_OPENAI_RESPONSES_DEPLOYMENT`, `AZURE_OPENAI_MINI_DEPLOYMENT`) rather than a generic mapping.

## Open Questions

1. Does the installed `@openai/agents` version support `session.connect({ url })` for custom WebRTC endpoints? Needs verification before implementing the hook change.
2. Does the Azure ephemeral token response use the same `client_secret.value` shape as direct OpenAI? Needs confirmation against Azure docs.
