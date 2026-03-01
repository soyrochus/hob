## Why

Enterprise deployments often cannot reach the OpenAI API directly but have an approved Azure OpenAI resource available. Hob currently hardcodes the direct OpenAI API across three call sites, blocking adoption in these environments. Adding Azure OpenAI as a configuration-only alternative unblocks enterprise use without changing the UI or runtime behaviour.

## What Changes

- Introduce `LLM_PROVIDER` env var (`openai` | `azure`) for explicit, rapid provider switching without touching credential variables
- When `LLM_PROVIDER` is not set, auto-detect the provider by checking for `OPENAI_API_KEY` first, then `AZURE_OPENAI_ENDPOINT`; if neither is found, throw a runtime exception
- Add provider-aware branching in the session endpoint (`/api/session`) to use Azure Realtime session URL and `api-key` header when provider is `azure`
- Add provider-aware branching in the responses proxy (`/api/responses`) to use `AzureOpenAI` client from the `openai` package and rewrite `body.model` to the Azure deployment name
- Extend the session endpoint response to include an optional `realtimeUrl` so the browser connects to the Azure WebRTC endpoint
- Update the `useRealtimeSession` hook's `getEphemeralKey` contract to accept `{ key, realtimeUrl? }` and pass the URL through to `session.connect()`
- Update `App.tsx`'s `fetchEphemeralKey` to forward the new `realtimeUrl` field
- Add `LLM_PROVIDER` and `AZURE_OPENAI_*` environment variable documentation to `.env.local`

## Capabilities

### New Capabilities

- `azure-openai-provider`: Configuration-driven provider switching between direct OpenAI API and Azure OpenAI. Supports explicit selection via `LLM_PROVIDER` env var for rapid switching, with auto-detection fallback based on credential presence (`OPENAI_API_KEY` → `AZURE_OPENAI_ENDPOINT`). Runtime exception if no provider can be resolved.

### Modified Capabilities
<!-- No existing openspec capabilities are affected at the spec level -->

## Impact

- **Files changed**: `src/app/api/session/route.ts`, `src/app/api/responses/route.ts`, `src/app/hooks/useRealtimeSession.ts`, `src/app/App.tsx`, `.env.local`
- **Dependencies**: No new packages — `AzureOpenAI` is already exported from the existing `openai` npm package
- **APIs**: The `/api/session` response gains an optional `realtimeUrl` field (additive, non-breaking)
- **Internal contract**: `ConnectOptions.getEphemeralKey` return type changes from `Promise<string>` to `Promise<{ key: string; realtimeUrl?: string }>` — this is internal-only and affects `useRealtimeSession.ts` and `App.tsx`
- **Risks**: Azure Realtime API and Responses API availability depends on the Azure subscription tier/region; the `openai` SDK's `session.connect({ url })` option needs verification against the installed `@openai/agents` version
