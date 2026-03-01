## 1. Provider Resolution

- [x] 1.1 Create `src/app/lib/resolveProvider.ts` with the `resolveProvider()` function implementing three-tier detection: `LLM_PROVIDER` explicit → `OPENAI_API_KEY` auto-detect → `AZURE_OPENAI_ENDPOINT` auto-detect → runtime exception
- [x] 1.2 Validate `LLM_PROVIDER` value — throw if set to anything other than `openai` or `azure`

## 2. Session Route (`/api/session`)

- [x] 2.1 Import `resolveProvider` and branch on returned provider in `src/app/api/session/route.ts`
- [x] 2.2 Implement Azure session token request: POST to `{AZURE_OPENAI_ENDPOINT}/openai/realtime/sessions?api-version={AZURE_OPENAI_API_VERSION}` with `api-key` header and `AZURE_OPENAI_REALTIME_DEPLOYMENT` as model
- [x] 2.3 Return `realtimeUrl` field in Azure mode pointing to `wss://{resource}.openai.azure.com/openai/v1/realtime?model={deployment-name}`
- [x] 2.4 Verify direct OpenAI path is unchanged when provider resolves to `openai`

## 3. Responses Route (`/api/responses`)

- [x] 3.1 Import `resolveProvider` and `AzureOpenAI` in `src/app/api/responses/route.ts`
- [x] 3.2 Implement `buildClient()` factory returning `AzureOpenAI` or `OpenAI` based on resolved provider
- [x] 3.3 Rewrite `body.model` to `AZURE_OPENAI_RESPONSES_DEPLOYMENT` when provider is `azure`
- [x] 3.4 Verify `structuredResponse` and `textResponse` work identically with both client types

## 4. Ephemeral Key Contract & WebRTC Hook

- [x] 4.1 Change `ConnectOptions.getEphemeralKey` return type from `Promise<string>` to `Promise<{ key: string; realtimeUrl?: string }>` in `src/app/hooks/useRealtimeSession.ts`
- [x] 4.2 Update `connect()` to destructure `{ key, realtimeUrl }` from `getEphemeralKey()` and pass `url` to `session.connect()` when present
- [x] 4.3 Update `fetchEphemeralKey` in `src/app/App.tsx` to return `{ key, realtimeUrl }` from the `/api/session` response
- [x] 4.4 Update all call sites passing `getEphemeralKey` to match the new return type

## 5. Configuration & Documentation

- [x] 5.1 Add `LLM_PROVIDER` and `AZURE_OPENAI_*` variables to `.env.example` (or `.env.local` docs) with comments explaining the three-tier detection logic
- [x] 5.2 Verify the app starts and connects successfully with `LLM_PROVIDER=openai` and existing `OPENAI_API_KEY`

## 6. SDK Verification

- [x] 6.1 Verify `@openai/agents` `session.connect({ url })` accepts a custom URL for WebRTC — check SDK source or docs
- [x] 6.2 Verify Azure ephemeral token response uses the same `client_secret.value` shape as direct OpenAI
