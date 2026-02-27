# SPEC002 — Azure OpenAI Connectivity

## Goal

Allow Hob to connect to **Azure OpenAI** as an alternative to the direct OpenAI API, without
breaking the existing direct-OpenAI path.

This is needed for enterprise deployments where the OpenAI API is not directly reachable but
an Azure OpenAI resource is available (e.g. a corporate environment with an approved Azure
tenant).

The switch between providers must be **configuration-only** — no code path changes at runtime,
no UI changes, no new UI elements.

---

## Background: What Needs to Change

Three independent call sites currently hardcode the OpenAI direct API:

| # | File | What it does | OpenAI-specific part |
| - | ---- | ------------ | -------------------- |
| 1 | `src/app/api/session/route.ts` | Mints an ephemeral Realtime session key | Hardcoded URL `https://api.openai.com/v1/realtime/sessions` + Bearer auth |
| 2 | `src/app/api/responses/route.ts` | Proxies Responses API calls (supervisor, guardrails) | `new OpenAI({ apiKey })` |
| 3 | `src/app/hooks/useRealtimeSession.ts` | Establishes the WebRTC connection | `session.connect({ apiKey: ek })` — SDK resolves to `api.openai.com` endpoint |

Each needs a provider-aware code path. The provider is selected by the presence of
`AZURE_OPENAI_*` environment variables; if they are absent the existing direct-OpenAI path
is used unchanged.

---

## Environment Variables

Add to `.env.local` (Azure path — all three required together):

```env
# Azure OpenAI — if set, takes precedence over OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_KEY=<your-azure-api-key>
AZURE_OPENAI_API_VERSION=2025-04-01-preview

# Azure deployment names (may differ from model names)
AZURE_OPENAI_REALTIME_DEPLOYMENT=gpt-4o-realtime-preview
AZURE_OPENAI_RESPONSES_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_MINI_DEPLOYMENT=gpt-4o-mini
```

Existing `.env.local` direct-OpenAI path (unchanged):

```env
OPENAI_API_KEY=sk-...
```

Detection logic (used in all three files):

```ts
const isAzure = !!process.env.AZURE_OPENAI_ENDPOINT;
```

---

## Change 1 — `src/app/api/session/route.ts`

**Current behaviour**: POSTs to `https://api.openai.com/v1/realtime/sessions` with a Bearer
token to get an ephemeral key, which the browser then uses to open the WebRTC connection.

**Azure behaviour**: POSTs to the Azure equivalent endpoint. The response shape is identical
so no downstream changes are needed.

Azure session endpoint format:
```
POST {AZURE_OPENAI_ENDPOINT}/openai/realtime/sessions?api-version={AZURE_OPENAI_API_VERSION}
Header: api-key: {AZURE_OPENAI_API_KEY}
Body:   { "model": "{AZURE_OPENAI_REALTIME_DEPLOYMENT}" }
```

### Before (current)

```ts
const response = await fetch(
  "https://api.openai.com/v1/realtime/sessions",
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-4o-realtime-preview-2025-06-03",
    }),
  }
);
```

### After

```ts
const isAzure = !!process.env.AZURE_OPENAI_ENDPOINT;

const url = isAzure
  ? `${process.env.AZURE_OPENAI_ENDPOINT}/openai/realtime/sessions?api-version=${process.env.AZURE_OPENAI_API_VERSION}`
  : "https://api.openai.com/v1/realtime/sessions";

const headers: Record<string, string> = isAzure
  ? { "api-key": process.env.AZURE_OPENAI_API_KEY!, "Content-Type": "application/json" }
  : { Authorization: `Bearer ${process.env.OPENAI_API_KEY}`, "Content-Type": "application/json" };

const model = isAzure
  ? process.env.AZURE_OPENAI_REALTIME_DEPLOYMENT!
  : "gpt-4o-realtime-preview-2025-06-03";

const response = await fetch(url, {
  method: "POST",
  headers,
  body: JSON.stringify({ model }),
});
```

---

## Change 2 — `src/app/api/responses/route.ts`

**Current behaviour**: Constructs `new OpenAI({ apiKey })` and calls
`openai.responses.create()` / `openai.responses.parse()`.

**Azure behaviour**: Construct `new AzureOpenAI({ ... })` instead. The `AzureOpenAI` class is
exported from the same `openai` npm package and exposes the same `responses` API surface.

> **Risk**: `openai.responses` on Azure requires API version `2025-04-01-preview` or later and
> the feature must be enabled on the Azure resource. Verify with the Azure admin before
> implementing. If unavailable, the supervisor and guardrail features will not work on Azure.

### Before (current)

```ts
import OpenAI from 'openai';
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
```

### After

```ts
import OpenAI, { AzureOpenAI } from 'openai';

function buildClient(): OpenAI {
  if (process.env.AZURE_OPENAI_ENDPOINT) {
    return new AzureOpenAI({
      endpoint: process.env.AZURE_OPENAI_ENDPOINT,
      apiKey: process.env.AZURE_OPENAI_API_KEY,
      apiVersion: process.env.AZURE_OPENAI_API_VERSION,
    });
  }
  return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

const openai = buildClient();
```

The `structuredResponse` and `textResponse` helpers are unchanged — they receive the client
instance and call `openai.responses.parse/create` identically.

### Model name in request body

The `body` forwarded from the client currently carries the model name set in the agent config
(e.g. `gpt-4.1`). On Azure these must be **deployment names**, not model names.

The proxy route should rewrite `body.model` when in Azure mode:

```ts
if (isAzure && body.model) {
  body.model = process.env.AZURE_OPENAI_RESPONSES_DEPLOYMENT!;
}
```

---

## Change 3 — `src/app/hooks/useRealtimeSession.ts`

**Current behaviour**: Passes the ephemeral key directly to `session.connect({ apiKey: ek })`.
The Agents SDK resolves this to `api.openai.com`.

**Azure behaviour**: The `OpenAIRealtimeWebRTC` transport must be pointed at the Azure WebRTC
endpoint. The SDK accepts a custom `url` via the transport constructor or via
`session.connect()` options.

Azure WebRTC endpoint format:
```
wss://<resource>.openai.azure.com/openai/v1/realtime?model=<deployment-name>
```

The `/api/session` route already returns an ephemeral token — that token is used identically.
Only the WebRTC target URL changes.

The app must tell the browser which URL to use. The cleanest way is to have `/api/session`
return the target WebRTC URL alongside the ephemeral key, so the hook does not need to know
about Azure at all.

### `/api/session` response shape (extended)

```ts
// Current shape (from OpenAI docs):
// { client_secret: { value: string, expires_at: number }, ... }

// Extended shape returned by our route:
{
  client_secret: { value: string, expires_at: number },
  realtimeUrl?: string   // only present for Azure; undefined = use SDK default
}
```

### `useRealtimeSession.ts` — `getEphemeralKey` interface change

The hook's `ConnectOptions.getEphemeralKey` currently returns `Promise<string>`. Extend it to
return a richer object so the URL can be passed through:

```ts
// Before
getEphemeralKey: () => Promise<string>;

// After
getEphemeralKey: () => Promise<{ key: string; realtimeUrl?: string }>;
```

### `connect()` call — Before

```ts
const ek = await getEphemeralKey();
// ...
await sessionRef.current.connect({ apiKey: ek });
```

### `connect()` call — After

```ts
const { key: ek, realtimeUrl } = await getEphemeralKey();
// ...
const connectOptions: Record<string, any> = { apiKey: ek };
if (realtimeUrl) connectOptions.url = realtimeUrl;
await sessionRef.current.connect(connectOptions);
```

### `App.tsx` — `fetchEphemeralKey` update

`App.tsx` owns the `fetchEphemeralKey` function that is passed as `getEphemeralKey`. It needs
to forward the new `realtimeUrl` field:

```ts
// Before
const fetchEphemeralKey = async (): Promise<string> => {
  const res = await fetch("/api/session");
  const data = await res.json();
  return data.client_secret.value;
};

// After
const fetchEphemeralKey = async () => {
  const res = await fetch("/api/session");
  const data = await res.json();
  return {
    key: data.client_secret.value,
    realtimeUrl: data.realtimeUrl,   // undefined on direct-OpenAI path
  };
};
```

---

## Summary of Files Changed

| File | Change |
| ---- | ------ |
| `.env.local` | Add 5 `AZURE_OPENAI_*` variables |
| `src/app/api/session/route.ts` | Branch on `AZURE_OPENAI_ENDPOINT`; use Azure URL + `api-key` header; return `realtimeUrl` |
| `src/app/api/responses/route.ts` | Branch on `AZURE_OPENAI_ENDPOINT`; use `AzureOpenAI` client; rewrite `body.model` |
| `src/app/hooks/useRealtimeSession.ts` | Accept `{ key, realtimeUrl }` from `getEphemeralKey`; pass `url` to `connect()` |
| `src/app/App.tsx` | Update `fetchEphemeralKey` return type to pass through `realtimeUrl` |

---

## Open Questions / Risks

| # | Question | Impact |
| - | -------- | ------ |
| 1 | Does the Azure subscription have the **Realtime API** enabled? Not all tiers/regions include it. | Blocker if absent |
| 2 | Is `openai.responses` (Responses API) available on the Azure deployment? Required for supervisor and guardrails. | Partial degradation if absent — realtime voice works, but supervisor and guardrails do not |
| 3 | Do the Azure deployment names match the model names used in agent configs (e.g. `gpt-4.1`, `o4-mini`)? | Must map deployment names explicitly per model |
| 4 | Does `OpenAIRealtimeWebRTC.connect({ url })` accept a custom URL in `@openai/agents` v0.0.5? | Must verify against SDK source before implementing Change 3; may require SDK upgrade |
| 5 | Does the Azure ephemeral token flow use the same `client_secret.value` response shape? | Should be confirmed against Azure docs before implementing Change 1 |

---

## Out of Scope

- UI controls for switching provider at runtime (configuration-only, via `.env`)
- Supporting both providers simultaneously
- Azure AD / managed identity authentication (spec covers API key auth only)
- Testing with Azure Government or sovereign cloud endpoints
