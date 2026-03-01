## ADDED Requirements

### Requirement: Three-tier provider detection
The system SHALL resolve the LLM provider using a three-tier strategy: (1) if `LLM_PROVIDER` is set to `openai` or `azure`, use that provider; (2) if `LLM_PROVIDER` is unset, auto-detect by checking for `OPENAI_API_KEY` first, then `AZURE_OPENAI_ENDPOINT`; (3) if no provider can be resolved, throw a runtime exception.

#### Scenario: Explicit provider selection — openai
- **WHEN** `LLM_PROVIDER` is set to `openai`
- **THEN** all three call sites (session, responses, realtime) MUST use the direct OpenAI API regardless of whether Azure variables are also present

#### Scenario: Explicit provider selection — azure
- **WHEN** `LLM_PROVIDER` is set to `azure`
- **THEN** all three call sites MUST use Azure OpenAI endpoints and authentication regardless of whether `OPENAI_API_KEY` is also present

#### Scenario: Invalid explicit provider value
- **WHEN** `LLM_PROVIDER` is set to a value other than `openai` or `azure`
- **THEN** the system MUST throw a runtime exception indicating the invalid value and listing valid options

#### Scenario: Auto-detect OpenAI first
- **WHEN** `LLM_PROVIDER` is not set and `OPENAI_API_KEY` is present
- **THEN** the system MUST use the direct OpenAI API

#### Scenario: Auto-detect Azure second
- **WHEN** `LLM_PROVIDER` is not set, `OPENAI_API_KEY` is absent, and `AZURE_OPENAI_ENDPOINT` is present
- **THEN** the system MUST use Azure OpenAI

#### Scenario: No provider configured
- **WHEN** `LLM_PROVIDER` is not set, `OPENAI_API_KEY` is absent, and `AZURE_OPENAI_ENDPOINT` is absent
- **THEN** the system MUST throw a runtime exception with a clear error message listing the expected environment variables

### Requirement: Azure environment variable configuration
The system SHALL require the following environment variables when operating in Azure mode: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_REALTIME_DEPLOYMENT`, `AZURE_OPENAI_RESPONSES_DEPLOYMENT`, and `AZURE_OPENAI_MINI_DEPLOYMENT`.

#### Scenario: All Azure variables present
- **WHEN** all six `AZURE_OPENAI_*` variables are set
- **THEN** the system MUST operate in Azure mode without errors

#### Scenario: Partial Azure variables
- **WHEN** the resolved provider is `azure` but required Azure variables (other than `AZURE_OPENAI_ENDPOINT`) are missing
- **THEN** the affected API route MUST return an error response rather than silently falling back to direct OpenAI

### Requirement: Azure session endpoint for ephemeral key
The session route (`/api/session`) SHALL POST to `{AZURE_OPENAI_ENDPOINT}/openai/realtime/sessions?api-version={AZURE_OPENAI_API_VERSION}` with an `api-key` header and a body containing the deployment name from `AZURE_OPENAI_REALTIME_DEPLOYMENT` when in Azure mode.

#### Scenario: Azure session token request
- **WHEN** a GET request is made to `/api/session` in Azure mode
- **THEN** the route MUST POST to the Azure Realtime sessions endpoint using the `api-key` header (not `Authorization: Bearer`) and the deployment name as the `model` field

#### Scenario: Direct OpenAI session token request unchanged
- **WHEN** a GET request is made to `/api/session` in direct OpenAI mode
- **THEN** the route MUST POST to `https://api.openai.com/v1/realtime/sessions` with `Authorization: Bearer` header, identical to current behavior

### Requirement: Session response includes realtime URL
The session route SHALL include an optional `realtimeUrl` field in its JSON response when operating in Azure mode. This URL MUST point to the Azure WebRTC endpoint in the format `wss://{resource}.openai.azure.com/openai/v1/realtime?model={deployment-name}`.

#### Scenario: Azure session response contains realtimeUrl
- **WHEN** the session route responds in Azure mode
- **THEN** the response JSON MUST include a `realtimeUrl` string field alongside the existing `client_secret` field

#### Scenario: Direct OpenAI session response omits realtimeUrl
- **WHEN** the session route responds in direct OpenAI mode
- **THEN** the response JSON MUST NOT include a `realtimeUrl` field (or it MUST be undefined)

### Requirement: Azure OpenAI client for responses proxy
The responses route (`/api/responses`) SHALL use `AzureOpenAI` from the `openai` package when in Azure mode. The client MUST be configured with `endpoint`, `apiKey`, and `apiVersion` from environment variables.

#### Scenario: Azure responses client construction
- **WHEN** a POST request is made to `/api/responses` in Azure mode
- **THEN** the route MUST use an `AzureOpenAI` client instance instead of the default `OpenAI` client

#### Scenario: Responses API surface unchanged
- **WHEN** the Azure client is used for responses
- **THEN** `structuredResponse` and `textResponse` helpers MUST work identically with both client types, requiring no downstream changes

### Requirement: Model name rewriting for Azure deployments
The responses route SHALL rewrite `body.model` to the value of `AZURE_OPENAI_RESPONSES_DEPLOYMENT` when in Azure mode, before forwarding the request to the SDK.

#### Scenario: Model name rewritten in Azure mode
- **WHEN** a responses request arrives with `body.model` set to a model name (e.g. `gpt-4.1`) in Azure mode
- **THEN** the route MUST replace `body.model` with the value of `AZURE_OPENAI_RESPONSES_DEPLOYMENT`

#### Scenario: Model name preserved in direct OpenAI mode
- **WHEN** a responses request arrives in direct OpenAI mode
- **THEN** `body.model` MUST be forwarded unchanged

### Requirement: Ephemeral key contract supports realtime URL
The `ConnectOptions.getEphemeralKey` interface SHALL return `Promise<{ key: string; realtimeUrl?: string }>` instead of `Promise<string>`. The `realtimeUrl` field is optional and only present when using Azure.

#### Scenario: getEphemeralKey returns object with URL in Azure mode
- **WHEN** `fetchEphemeralKey` is called and the server returns a `realtimeUrl`
- **THEN** it MUST return `{ key: <ephemeral-key>, realtimeUrl: <url> }`

#### Scenario: getEphemeralKey returns object without URL in direct mode
- **WHEN** `fetchEphemeralKey` is called and the server does not return a `realtimeUrl`
- **THEN** it MUST return `{ key: <ephemeral-key> }` with `realtimeUrl` undefined

### Requirement: WebRTC connection uses server-provided URL
The realtime session hook SHALL pass the `realtimeUrl` (when present) as the `url` option to `session.connect()`, directing the WebRTC connection to the Azure endpoint.

#### Scenario: Azure WebRTC connection
- **WHEN** `getEphemeralKey` returns a `realtimeUrl`
- **THEN** `session.connect()` MUST be called with `{ apiKey: key, url: realtimeUrl }`

#### Scenario: Direct OpenAI WebRTC connection
- **WHEN** `getEphemeralKey` returns without a `realtimeUrl`
- **THEN** `session.connect()` MUST be called with `{ apiKey: key }` only, allowing the SDK to use its default endpoint
