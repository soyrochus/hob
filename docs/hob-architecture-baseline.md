# Architecture Baseline — Hob

> **Status**: Baseline documentation of the application as it currently stands.
> **Purpose**: This document serves as an implementation guideline. Each functional requirement is mapped to the exact code that satisfies it, so that when package versions are updated and the implementation breaks, the correct behavior can be restored.
>
> This application is a fork of [OpenAI's Realtime API Agents Demo](https://github.com/openai/openai-realtime-agents), adapted into **Hob**.

---

## 1. Overview

Hob is a **voice-first multi-agent application** built on the OpenAI Realtime API. It enables low-latency, streaming voice conversations with AI agents that can call tools, hand off between each other, and be supervised by higher-intelligence text-based models.

### Technology Stack

| Layer | Technology |
| ----- | ---------- |
| Framework | Next.js 15 (App Router) |
| Language | TypeScript (strict mode) |
| UI | React 19, Tailwind CSS |
| Agent Orchestration | `@openai/agents/realtime` (OpenAI Agents SDK) |
| Voice Transport | WebRTC via OpenAI Realtime API |
| Realtime Model | `gpt-4o-realtime-preview-2025-06-03` |
| Transcription Model | `gpt-4o-mini-transcribe` |
| Tool Execution Model | `gpt-4.1` (via `/api/responses`) |
| Guardrail Model | `gpt-4o-mini` (via `/api/responses`) |
| Schema Validation | Zod |
| State Management | React Context API |

---

## 2. Top-Level Project Structure

```
/
├── src/
│   └── app/
│       ├── App.tsx                  # Root client component — session orchestration, layout
│       ├── page.tsx                 # Next.js page; wraps App in context providers
│       ├── layout.tsx               # Root HTML layout
│       ├── types.ts                 # Core TypeScript enums and interfaces
│       ├── api/
│       │   ├── session/route.ts     # Creates ephemeral OpenAI Realtime sessions
│       │   └── responses/route.ts   # Proxy to OpenAI Responses API (tools, guardrails)
│       ├── agentConfigs/            # All agent scenario definitions
│       │   ├── index.ts             # Scenario registry (allAgentSets, defaultAgentSetKey)
│       │   ├── guardrails.ts        # Output moderation guardrail factory
│       │   ├── defaultAssistant/    # General-purpose voice assistant (default scenario)
│       │   │   ├── index.ts         # RealtimeAgent definition
│       │   │   └── hostedTools.ts   # webSearch, codeInterpreter, fileSearch tool definitions
│       │   ├── chatSupervisor/      # Two-tier realtime + text-supervisor demo
│       │   ├── customerServiceRetail/ # Multi-agent retail customer service demo
│       │   └── simpleHandoff.ts     # Minimal agent handoff demo
│       ├── components/              # React UI components
│       │   ├── Transcript.tsx       # Conversation history display
│       │   ├── Events.tsx           # Raw SDK event log (debug mode)
│       │   ├── Avatar.tsx           # Animated avatar driven by audio level
│       │   ├── BottomToolbar.tsx    # Connection controls, PTT, audio toggle
│       │   └── GuardrailChip.tsx    # Inline moderation status chip per message
│       ├── contexts/
│       │   ├── TranscriptContext.tsx  # Conversation UI state
│       │   └── EventContext.tsx       # Developer event log state
│       ├── hooks/
│       │   ├── useRealtimeSession.ts      # SDK session lifecycle and event wiring
│       │   ├── useHandleSessionHistory.ts # Translates SDK events → transcript state
│       │   └── useAudioDownload.ts        # Records and downloads the conversation audio
│       └── lib/
│           ├── audioUtils.ts        # WebM → WAV conversion
│           ├── codecUtils.ts        # SDP-level codec preference injection
│           ├── envSetup.ts          # Environment setup helpers
│           └── resolveProvider.ts   # OpenAI vs Azure provider selection
├── docs/                            # Documentation
├── package.json
└── tsconfig.json
```

---

## 3. Runtime Architecture

### 3.1 Session Lifecycle

```
Browser                     Next.js Server              OpenAI
  │                               │                        │
  │── GET /api/session ──────────>│                        │
  │                               │── POST /realtime/sessions ──>│
  │                               │<── ephemeral key ───────────│
  │<── { client_secret } ────────│                        │
  │                               │                        │
  │── WebRTC negotiation (SDP) ─────────────────────────>│
  │<── audio stream (bidirectional) ───────────────────────│
```

1. The browser calls `GET /api/session`, which proxies to OpenAI and returns a short-lived ephemeral key (1 hour TTL).
2. The browser uses that key to establish a **WebRTC peer connection** directly with OpenAI — audio is end-to-end encrypted and does not pass through the Next.js server.
3. All subsequent intelligence (responses, tool calls, handoffs) streams back over the same WebRTC connection.

**Key implementation** (`src/app/api/session/route.ts`):

- POSTs to `https://api.openai.com/v1/realtime/sessions` with `model: "gpt-4o-realtime-preview-2025-06-03"`.
- Supports Azure OpenAI via `resolveProvider()` — when Azure, builds a `wss://` URL and returns it as `realtimeUrl`.

### 3.2 Tool Execution via Responses API

Tools that require external computation call the `/api/responses` server-side proxy:

```
Browser (tool.execute())         Next.js Server          OpenAI Responses API
  │                                    │                        │
  │── POST /api/responses ────────────>│                        │
  │   { model, input, tools }          │── openai.responses.create() ──>│
  │                                    │<── { output }──────────────────│
  │<── { result: textSummary } ────────│                        │
```

This route also serves guardrail classification calls. Both use `openai.responses.create()` (non-streaming). For structured output (guardrails), it uses `openai.responses.parse()` with a Zod schema.

---

## 4. Agent Architecture

### 4.1 Agent Definition Model

All agents are instances of `RealtimeAgent` from `@openai/agents/realtime`. An agent is defined by:

```typescript
new RealtimeAgent({
  name: string,              // Unique identifier
  voice: string,             // TTS voice (e.g. "sage")
  instructions: string,      // System prompt / persona
  tools: Tool[],             // Callable tool objects created with tool()
  handoffs?: RealtimeAgent[], // Agents this agent can transfer to
  handoffDescription?: string, // Shown to other agents when routing
})
```

Tools are created with the `tool()` helper from `@openai/agents/realtime`:

```typescript
tool({
  name: string,
  description: string,
  parameters: { type: 'object', properties: {...}, required: [...] },
  execute: async (input) => result,  // runs in browser process
})
```

### 4.2 The Four Scenarios

Scenarios are registered in `src/app/agentConfigs/index.ts` and selected via `?agentConfig=` URL parameter or UI dropdown.

#### Default Assistant (`defaultAssistant`) — Primary Scenario

A single `RealtimeAgent` with three hosted tools. This is the default scenario.

```
User (voice/text) ──> assistantAgent (gpt-4o-realtime)
                           │
                    ┌──────┴──────────────────┐
                    │                          │
               webSearch              codeInterpreter
               fileSearch
                    │                          │
                POST /api/responses    POST /api/responses
                (gpt-4.1)             (gpt-4.1)
```

Each tool's `execute()` function calls `/api/responses` with `gpt-4.1`, runs the relevant hosted tool (web_search, code_interpreter, file_search), extracts only the text output via `extractOutputText()`, and returns `{ result: text }` to the realtime model. Raw intermediate results never surface in the UI.

#### Simple Handoff (`simpleHandoff`)

```
greeterAgent ──handoff──> haikuWriterAgent
```

Minimal reference implementation of agent-to-agent transfer.

#### Chat Supervisor (`chatSupervisor`)

```
User (voice) ──> chatAgent (gpt-4o-realtime-mini)
                      │ tool: getNextResponseFromSupervisor()
                 POST /api/responses
                      │
               supervisorAgent (gpt-4.1, text model)
                      │ tools: lookupPolicy, getUserAccountInfo, etc.
```

Realtime mini handles greetings; complex queries are forwarded to a text supervisor with full history.

#### Customer Service Retail (`customerServiceRetail`)

Fully-connected multi-agent network: `authentication ↔ returns ↔ sales ↔ simulatedHuman`.

---

## 5. Functional Specification: Implementation Map

This section documents exactly **how the implementation guarantees each stated functional requirement**. Use this as the authoritative re-implementation guide.

---

### 5.1 Bidirectional Real-Time Voice

**Requirement**: Full-duplex voice; user speaks and AI responds simultaneously with audio.

**How**:

- `OpenAIRealtimeWebRTC` from `@openai/agents/realtime` creates an `RTCPeerConnection`.
- WebRTC is inherently full-duplex — microphone audio flows to OpenAI while AI audio flows back simultaneously.
- AI audio is rendered through a hidden `<audio>` element created in `App.tsx`:

  ```typescript
  const el = document.createElement('audio');
  el.autoplay = true;
  el.style.display = 'none';
  document.body.appendChild(el);
  ```

  This element is passed to `OpenAIRealtimeWebRTC` as `audioElement`.

- The `changePeerConnection` hook in `useRealtimeSession.ts:132` injects codec preferences into the SDP before offer/answer negotiation via `applyCodecPreferences()` (`src/app/lib/codecUtils.ts`).

---

### 5.2 Live Streaming Transcription (User Speech → Right Side)

**Requirement**: User speech transcribed live and displayed as streaming text on the right.

**How**:

- Session config enables server-side transcription (`useRealtimeSession.ts:139`):

  ```typescript
  inputAudioTranscription: { model: 'gpt-4o-mini-transcribe' }
  ```

- When a new user turn begins, the SDK fires `history_added` → `handleHistoryAdded()` (`useHandleSessionHistory.ts:88`):
  - If user role and no text yet, stores placeholder `"[Transcribing...]"` via `addTranscriptMessage(itemId, role, text)`.
- As transcript words arrive, `history_updated` → `handleHistoryUpdated()` updates the item text with `updateTranscriptMessage(itemId, text, false)` (replace, not append).
- Finalization: `conversation.item.input_audio_transcription.completed` transport event → `handleTranscriptionCompleted()` (`useHandleSessionHistory.ts:136`):
  - Sets final text (or `"[inaudible]"` if empty).
  - Calls `updateTranscriptMessage(itemId, finalTranscript, false)` — **replace mode** (`false` means overwrite, not delta).
  - Calls `updateTranscriptItem(itemId, { status: 'DONE' })`.
- User messages are rendered `items-end` (right-aligned) in `Transcript.tsx:122-126`.

---

### 5.3 Live Streaming AI Response (AI Audio → Left Side)

**Requirement**: AI generates audio responses in real time; streamed text displayed on left.

**How**:

- When the AI starts speaking, `history_added` fires → `handleHistoryAdded()` stores an assistant `MESSAGE` item.
- As the AI speaks, `response.audio_transcript.delta` transport event → `handleTranscriptionDelta()` (`useHandleSessionHistory.ts:128`):

  ```typescript
  updateTranscriptMessage(itemId, deltaText, true);  // append=true (streaming)
  ```

- Finalization: `response.audio_transcript.done` transport event → `handleTranscriptionCompleted()`:
  - Replaces streaming text with the final stabilized transcript.
  - Sets `status: 'DONE'`.
- These transport events are routed in `useRealtimeSession.ts:46-66` inside `handleTransportEvent()`, which listens to the `transport_event` SDK event.
- Assistant messages are rendered `items-start` (left-aligned) in `Transcript.tsx:122-126`.

**Critical**: The `isDelta` boolean in `updateTranscriptMessage` (`TranscriptContext.tsx:67`) controls streaming vs finalization:

```typescript
title: append ? (item.title ?? "") + newText : newText
```

Streaming passes `true` (append); finalization passes `false` (replace).

---

### 5.4 Interruption

**Requirement**: Interruption immediately halts AI speech generation and shifts control back to the user.

**How**:

- `useRealtimeSession.ts:167` exposes:

  ```typescript
  const interrupt = () => { sessionRef.current?.interrupt(); }
  ```

- `session.interrupt()` is a method on `RealtimeSession` from `@openai/agents/realtime` that sends the appropriate signal to stop generation.
- Called in `App.tsx` in two places:
  - `handleSendTextMessage()` (line 325): before sending typed text.
  - `handleTalkButtonDown()` (line 337): when PTT button is pressed.
- For VAD mode, the server also interrupts automatically when VAD detects the user speaking.

---

### 5.5 Voice Activity Detection (VAD)

**Requirement**: System automatically detects when user finishes speaking and triggers AI response.

**How**:

- Session is configured via `session.update` event sent through `sendEvent()` in `updateSession()` (`App.tsx:295`):

  ```typescript
  {
    type: 'server_vad',
    threshold: 0.9,
    prefix_padding_ms: 300,
    silence_duration_ms: 500,
    create_response: true,
  }
  ```

- `create_response: true` means the server automatically triggers AI response generation when the user stops speaking — no client-side trigger needed.
- When `isPTTActive` is `true`, `turn_detection` is set to `null`, disabling VAD entirely.

---

### 5.6 Push-to-Talk (PTT) Mode

**Requirement**: Alternative to VAD; explicit button-hold interaction.

**How**:

- `handleTalkButtonDown()` (`App.tsx:336`):
  1. Calls `interrupt()` to stop any ongoing AI response.
  2. Sends `input_audio_buffer.clear` — discards any audio buffered before button press.
- `handleTalkButtonUp()` (`App.tsx:346`):
  1. Sends `input_audio_buffer.commit` — marks the audio segment as complete.
  2. Sends `response.create` — triggers AI response generation.
- PTT and VAD are mutually exclusive: VAD is disabled (`turn_detection: null`) when PTT is active.

---

### 5.7 Conversation Log: Finalized Turns Only

**Requirement**: Only finalized turns are committed to the persistent log; streaming artifacts are not stored separately.

**How**:

- Each turn creates exactly one `TranscriptItem` keyed by `itemId` (from the SDK event).
- `addTranscriptMessage()` (`TranscriptContext.tsx:44`) guards against duplicates:

  ```typescript
  if (prev.some((log) => log.itemId === itemId && log.type === "MESSAGE")) {
    return prev;  // skip duplicate
  }
  ```

- Streaming updates mutate the `title` field of the existing item in place — they do not create new items.
- `status: "IN_PROGRESS"` → `status: "DONE"` transition happens only on the `*completed` / `*.done` transport events.
- The rendered list is sorted by `createdAtMs` (`Transcript.tsx:102`) so the logical order of dialogue is always preserved regardless of update ordering.

---

### 5.8 Left/Right Visual Layout

**Requirement**: AI outputs on left, user inputs on right.

**How** (`Transcript.tsx:120-163`):

```typescript
const isUser = role === "user";
const containerClasses = `flex justify-end flex-col ${
  isUser ? "items-end" : "items-start"
}`;
const bubbleBase = `max-w-lg p-3 ${
  isUser ? "bg-gray-900 text-gray-100" : "bg-gray-100 text-black"
}`;
```

- `items-end` = right-aligned (user).
- `items-start` = left-aligned (assistant).
- Hidden items (`isHidden: true`) are skipped: `if (isHidden) return null`.

---

### 5.9 Tool Invocation: Breadcrumb (Not Message) Pattern

**Requirement**: Tool calls appear as log entries (not dialogue messages); raw tool output is not exposed.

**How**:

- `agent_tool_start` SDK event → `handleAgentToolStart()` (`useHandleSessionHistory.ts:70`):

  ```typescript
  addTranscriptBreadcrumb(`function call: ${function_name}`, function_args);
  ```

- `agent_tool_end` SDK event → `handleAgentToolEnd()` (`useHandleSessionHistory.ts:80`):

  ```typescript
  addTranscriptBreadcrumb(`function call result: ${name}`, maybeParseJson(result));
  ```

- Breadcrumbs are type `"BREADCRUMB"`, rendered as monospace metadata lines — not chat bubbles. They are collapsible (expand to show JSON payload on click) but collapsed by default.
- The tool's `execute()` function (in `hostedTools.ts`) calls `/api/responses` and returns only the extracted text summary:

  ```typescript
  const text = extractOutputText(response);
  return { result: text || 'No result available.' };
  ```

  `extractOutputText()` strips the full API response envelope and returns only message text content. The realtime model receives `{ result: "..." }` as the tool output, not raw API JSON.

- The realtime model then synthesizes a voice/text response using that summary. This synthesized response is stored as a normal `MESSAGE` item.

---

### 5.10 Tool Execution: Server-Side Proxy

**Requirement**: Tool computation occurs externally; result injected as context to the AI.

**How**:

- Tool `execute()` functions in `hostedTools.ts` call `callResponses()`, which POSTs to `/api/responses`:

  ```typescript
  await fetch('/api/responses', {
    method: 'POST',
    body: JSON.stringify({ model: 'gpt-4.1', input: prompt, tools: [...] })
  });
  ```

- `/api/responses/route.ts` uses `openai.responses.create()` (non-streaming, server-side) to run the actual tool loop on OpenAI infrastructure.
- `parallel_tool_calls: false` is always set to avoid ordering issues.
- The SDK's `agent_tool_end` event signals that the result has been injected back into the conversation history for the realtime model to consume.

---

### 5.11 Output Guardrails

**Requirement**: Safety moderation on AI output; corrective injection if triggered; UI status indicator.

**How**:

- A guardrail is created per scenario in `App.tsx:251` via `createModerationGuardrail(companyName, profile)` from `guardrails.ts`.
- Passed to `RealtimeSession` as `outputGuardrails: [guardrail]`.
- When the realtime model finishes a response, the SDK calls `guardrail.execute({ agentOutput })`, which:
  1. POSTs to `/api/responses` with `gpt-4o-mini` and a structured Zod schema format.
  2. Parses the response with `GuardrailOutputZod` → `{ moderationCategory, moderationRationale }`.
  3. Returns `{ tripwireTriggered: boolean, outputInfo: result }`.
- If `tripwireTriggered`, the SDK fires `guardrail_tripped` → `handleGuardrailTripped()` (`useHandleSessionHistory.ts:163`):
  - Finds the offending assistant message by `itemId`.
  - Updates it: `updateTranscriptItem(itemId, { guardrailResult: { status: 'DONE', category, rationale } })`.
  - The SDK also injects a corrective message into the conversation, which appears as a `BREADCRUMB` (detected by `sketchilyDetectGuardrailMessage()` in `handleHistoryAdded`).
- `GuardrailChip` renders below the message bubble when `guardrailResult` is present.
- Guardrail runs **asynchronously** after response completion — it does not block audio playback.
- The `general` profile (used by `defaultAssistant`) allows informational/journalistic violence content; the `company` profile (used by retail/supervisor) also flags `OFF_BRAND` content.

---

### 5.12 Agent Handoff

**Requirement**: Agent transfers route the session to a new agent; breadcrumb recorded.

**How**:

- Agents declare `handoffs: [otherAgent]` in their `RealtimeAgent` definition.
- When an agent calls a `transfer_to_{name}` function, the SDK fires `agent_handoff` → `handleAgentHandoff()` (`useRealtimeSession.ts:83`):

  ```typescript
  const agentName = lastMessage.name.split("transfer_to_")[1];
  callbacks.onAgentHandoff?.(agentName);
  ```

- `App.tsx` handles `onAgentHandoff` by setting `handoffTriggeredRef.current = true` and updating `selectedAgentName`.
- The `useEffect` watching `selectedAgentName` calls `addTranscriptBreadcrumb(\`Agent: ${selectedAgentName}\`, currentAgent)` and `updateSession(false)` (no re-greeting after handoff).

---

## 6. Voice & Audio System

### 6.1 Transport

- Audio uses **WebRTC** (`RTCPeerConnection`) via `OpenAIRealtimeWebRTC` from the SDK.
- Remote audio is rendered through a hidden `<audio>` element injected into the DOM in `App.tsx` (via `React.useMemo` on first browser render).
- Codec negotiation is configurable: **opus 48kHz** (default) or **PCMU/PCMA 8kHz** (narrow-band, PSTN simulation), controlled by `?codec=` URL parameter and applied in `codecUtils.ts` via the `changePeerConnection` hook.

### 6.2 Voice Activity Detection (VAD)

The default mode uses server-side VAD, configured via `session.update`:

| Parameter | Value |
| --------- | ----- |
| Type | `server_vad` |
| Threshold | 0.9 |
| Prefix padding | 300 ms |
| Silence duration | 500 ms |
| Create response | `true` |

PTT mode (`isPTTActive`) sets `turn_detection: null`, disabling VAD.

### 6.3 Transcription

User speech is transcribed by `gpt-4o-mini-transcribe`. Deltas are received as SDK history events. The finalized transcript is committed on `conversation.item.input_audio_transcription.completed`. Empty transcripts fall back to `[inaudible]`.

### 6.4 Audio Mute

- The `<audio>` element `muted` property and `session.mute(bool)` are kept in sync via effects in `App.tsx`.
- Mute is re-synced on connect (`sessionStatus === 'CONNECTED'`) to ensure the SDK transport receives the correct state after a fresh connection.

### 6.5 Audio Recording & Download

1. When session connects, `startRecording(remoteStream)` is called with the `<audio>` element's `srcObject`.
2. `useAudioDownload` merges mic + remote streams via the Web Audio API (`AudioContext`).
3. Records as WebM with `MediaRecorder`.
4. On download, `audioUtils.ts` converts the WebM blob to WAV.

---

## 7. State Management

### 7.1 Context Providers

Both providers are mounted at `page.tsx` level, wrapping `App`.

**TranscriptContext** (`src/app/contexts/TranscriptContext.tsx`) — owns the conversation UI model:

| Operation | Signature | Behavior |
| --------- | --------- | -------- |
| `addTranscriptMessage` | `(itemId, role, text, isHidden?)` | Creates a `MESSAGE` item; no-op if `itemId` already exists |
| `updateTranscriptMessage` | `(itemId, text, isDelta)` | Appends if `isDelta=true`, replaces if `false` |
| `addTranscriptBreadcrumb` | `(title, data?)` | Creates a `BREADCRUMB` item with a fresh UUID |
| `updateTranscriptItem` | `(itemId, partial)` | Merges partial properties into any item type |
| `toggleTranscriptItemExpand` | `(itemId)` | Toggles `expanded` for collapsible breadcrumbs |

**EventContext** (`src/app/contexts/EventContext.tsx`) — owns the developer event log. Used exclusively by `Events.tsx` (debug mode only).

### 7.2 TranscriptItem Type

```typescript
interface TranscriptItem {
  itemId: string;
  type: "MESSAGE" | "BREADCRUMB";
  role?: "user" | "assistant";     // only on MESSAGE
  title?: string;                   // display text
  data?: Record<string, any>;      // structured payload (breadcrumbs)
  expanded: boolean;
  timestamp: string;               // human-readable HH:MM:SS.mmm
  createdAtMs: number;             // for sort ordering
  status: "IN_PROGRESS" | "DONE";
  isHidden: boolean;
  guardrailResult?: GuardrailResultType;
}
```

### 7.3 Session State (local to App.tsx)

| State variable | Type | Purpose |
| -------------- | ---- | ------- |
| `sessionStatus` | `"DISCONNECTED" \| "CONNECTING" \| "CONNECTED"` | Connection lifecycle |
| `selectedAgentConfigSet` | `RealtimeAgent[]` | Active agent scenario |
| `selectedAgentName` | `string` | Currently active agent in session |
| `isPTTActive` | `boolean` | PTT mode enabled |
| `isPTTUserSpeaking` | `boolean` | User holding PTT button |
| `isDebugMode` | `boolean` | Show Events panel vs Avatar |

### 7.4 Persistent Preferences (localStorage)

| Key | Stored value |
| --- | ------------ |
| `pushToTalkUI` | PTT mode preference |
| `logsExpanded` | Event panel open/closed |
| `audioPlaybackEnabled` | Speaker output on/off |
| `debugMode` | Events panel vs Avatar display |

---

## 8. UI Layer

### 8.1 Layout

```
┌─────────────────────────────────────────────────┐
│  [Scenario ▼]  [Agent ▼]                 [Logo] │  ← Top bar
├──────────────────────────┬──────────────────────┤
│                          │                      │
│      Transcript          │  Avatar (default)    │
│   (messages + crumbs)    │  or Events (debug)   │
│                          │                      │
├──────────────────────────┴──────────────────────┤
│  [Connect]  [PTT □]  [🔊]  [Debug □]  [Codec ▼] │  ← Bottom toolbar
└─────────────────────────────────────────────────┘
```

The right panel shows the `Avatar` component by default. It switches to the `Events` debug panel when `isDebugMode` is `true` (toggled via the Debug checkbox in `BottomToolbar`).

### 8.2 Components

| Component | File | Responsibility |
| --------- | ---- | -------------- |
| `App` | `App.tsx` | Root layout, session orchestration, event wiring |
| `Transcript` | `Transcript.tsx` | Message bubbles (left/right), breadcrumbs, text input, auto-scroll |
| `Events` | `Events.tsx` | Collapsible raw SDK event log with JSON drill-down (debug mode only) |
| `Avatar` | `Avatar.tsx` | Animated avatar image driven by AI audio level (default right panel) |
| `BottomToolbar` | `BottomToolbar.tsx` | Connection controls, PTT toggle, audio on/off, debug mode, codec selector |
| `GuardrailChip` | `GuardrailChip.tsx` | Inline moderation status per assistant message bubble |

---

## 9. Key Hooks

### `useRealtimeSession` (`hooks/useRealtimeSession.ts`)

Manages the SDK `RealtimeSession` lifecycle. **This is where all SDK events are wired up.**

Key responsibilities:

- Creates `RealtimeSession` with `OpenAIRealtimeWebRTC` transport, model config, and output guardrails.
- Wires SDK events in a `useEffect` watching `sessionRef.current`:
  - `error` → log
  - `agent_handoff` → `handleAgentHandoff` → `callbacks.onAgentHandoff`
  - `agent_tool_start` → `historyHandlers.handleAgentToolStart`
  - `agent_tool_end` → `historyHandlers.handleAgentToolEnd`
  - `history_updated` → `historyHandlers.handleHistoryUpdated`
  - `history_added` → `historyHandlers.handleHistoryAdded`
  - `guardrail_tripped` → `historyHandlers.handleGuardrailTripped`
  - `transport_event` → `handleTransportEvent` (routes `conversation.item.input_audio_transcription.completed`, `response.audio_transcript.done`, `response.audio_transcript.delta`)
- Exposes: `connect`, `disconnect`, `sendUserText`, `sendEvent`, `mute`, `pushToTalkStart`, `pushToTalkStop`, `interrupt`.

### `useHandleSessionHistory` (`hooks/useHandleSessionHistory.ts`)

Translates SDK events into `TranscriptContext` state updates. **This is where the conversation log semantics are enforced.**

Returned as a `useRef` (`handlersRef`) to avoid stale closure issues when handlers are registered.

| Handler | Triggered by | Action |
| ------- | ------------ | ------ |
| `handleHistoryAdded` | `history_added` | Creates a `MESSAGE` item (or `BREADCRUMB` for guardrail corrections) |
| `handleHistoryUpdated` | `history_updated` | Replaces text on existing item (not append) |
| `handleTranscriptionDelta` | `response.audio_transcript.delta` | Appends delta text to AI message |
| `handleTranscriptionCompleted` | `*.completed` / `*.done` transport events | Finalizes text, sets `status: DONE` |
| `handleAgentToolStart` | `agent_tool_start` | Adds breadcrumb `function call: {name}` |
| `handleAgentToolEnd` | `agent_tool_end` | Adds breadcrumb `function call result: {name}` |
| `handleGuardrailTripped` | `guardrail_tripped` | Updates assistant message with `guardrailResult` |

### `useAudioDownload` (`hooks/useAudioDownload.ts`)

Merges mic and remote audio via `AudioContext`, records as WebM, exposes WAV download.

---

## 10. API Routes

| Route | Method | Purpose |
| ----- | ------ | ------- |
| `/api/session` | GET | Creates OpenAI Realtime session; returns ephemeral `client_secret` (and `realtimeUrl` for Azure) |
| `/api/responses` | POST | Proxies to OpenAI Responses API; handles both structured (Zod/JSON schema) and plain text responses |

Both routes support Azure OpenAI via `resolveProvider()` in `src/app/lib/resolveProvider.ts`.

---

## 11. Data Flow Summary

### Voice input → transcript

```
Microphone
  └─ WebRTC → OpenAI VAD → server-side transcription (gpt-4o-mini-transcribe)
                │
                ├─ [history_added event]
                │    └─ handleHistoryAdded() → addTranscriptMessage(id, "user", "[Transcribing...]")
                │
                ├─ [history_updated events]
                │    └─ handleHistoryUpdated() → updateTranscriptMessage(id, text, false)
                │
                └─ [conversation.item.input_audio_transcription.completed transport event]
                     └─ handleTranscriptionCompleted() → updateTranscriptMessage(id, final, false)
                                                       → updateTranscriptItem(id, { status: 'DONE' })
```

### AI response → audio + transcript

```
OpenAI generates response
  ├─ audio stream → <audio> element → speaker
  │
  ├─ [history_added event]
  │    └─ handleHistoryAdded() → addTranscriptMessage(id, "assistant", "")
  │
  ├─ [response.audio_transcript.delta transport events]
  │    └─ handleTranscriptionDelta() → updateTranscriptMessage(id, delta, true)  ← append
  │
  ├─ [response.audio_transcript.done transport event]
  │    └─ handleTranscriptionCompleted() → updateTranscriptMessage(id, final, false) ← replace
  │                                      → updateTranscriptItem(id, { status: 'DONE' })
  │
  └─ [guardrail check runs async]
       └─ guardrail.execute() → POST /api/responses (gpt-4o-mini)
            ├─ tripwire=false → no-op (message stays)
            └─ tripwire=true → handleGuardrailTripped() → updateTranscriptItem with guardrailResult
```

### Tool call

```
Realtime model decides to call a tool
  │
  ├─ [agent_tool_start event]
  │    └─ handleAgentToolStart() → addTranscriptBreadcrumb("function call: {name}", args)
  │
  ├─ tool.execute() runs in browser
  │    └─ POST /api/responses (gpt-4.1 + hosted tool)
  │         └─ extractOutputText() → return { result: textSummary }
  │
  ├─ [agent_tool_end event]
  │    └─ handleAgentToolEnd() → addTranscriptBreadcrumb("function call result: {name}", result)
  │
  └─ SDK injects result into conversation history → realtime model synthesizes response
       └─ [normal AI response flow above]
```

### Agent handoff

```
Agent calls transfer_to_{name}
  └─ [agent_handoff event]
       └─ handleAgentHandoff() → extract name from "transfer_to_" prefix
                               → callbacks.onAgentHandoff(agentName)
                               → App: setSelectedAgentName(agentName)
                               → addTranscriptBreadcrumb("Agent: {name}", agentDef)
                               → updateSession(false)  ← no re-greeting
```

---

## 12. Configuration & Build

- **TypeScript**: strict mode, target ES2017, path alias `@/*` → `./src/*`
- **Tailwind CSS**: utility classes only, no custom theme
- **Environment variables**: `OPENAI_API_KEY` (required); Azure vars if `resolveProvider()` returns `"azure"`
- **Dev server**: `npm run dev` (Next.js on port 3000)
- **Agent scenario selection**: URL parameter `?agentConfig=<key>` or UI dropdown
- **Codec selection**: URL parameter `?codec=opus` (default) or `?codec=pcmu`; requires page reload to reconnect

### Agent Registry

```typescript
// src/app/agentConfigs/index.ts
export const allAgentSets: Record<string, RealtimeAgent[]> = {
  defaultAssistant,
  simpleHandoff,
  customerServiceRetail,
  chatSupervisor,
};
export const defaultAgentSetKey = 'defaultAssistant';
```

To add a scenario: export a `RealtimeAgent[]` array from a new file, register it in this map.

---

## 13. Notable Design Patterns

1. **Breadcrumb pattern** — Tool calls, handoffs, and guardrail events are embedded as collapsible monospace metadata items (`BREADCRUMB`) in the transcript stream, visually separate from chat message bubbles (`MESSAGE`). This keeps the conversation log clean while preserving a full audit trail.

2. **itemId-keyed, status-driven transcript items** — Each SDK conversation item maps 1:1 to a `TranscriptItem`. Streaming updates mutate the single item in place via `itemId`. The `status` field (`IN_PROGRESS` / `DONE`) tracks the item's lifecycle and guards against duplicate creation.

3. **Dual update modes in `updateTranscriptMessage`** — The `isDelta: boolean` parameter separates streaming (append) from finalization (replace). This prevents audio transcript deltas from doubling up text when the completed event arrives.

4. **Handlers held in a `useRef`** — `useHandleSessionHistory` returns a `useRef` rather than raw functions. This gives the SDK event listeners stable function references that always reflect the latest closure state, avoiding stale-closure bugs in long-running sessions.

5. **Tool mediation via Responses API** — Hosted tools (webSearch, codeInterpreter, fileSearch) run server-side via `/api/responses` and return only a text summary to the realtime model. The raw intermediate steps (search results, code execution) are never surfaced to the UI or to the model's context beyond the summary.

6. **Async guardrails** — Output moderation runs after response completion and does not block audio playback. The `GuardrailChip` updates asynchronously; the message is visible immediately while the chip shows a pending state.

7. **Two-tier agent architecture** (chatSupervisor scenario) — Fast/cheap realtime model for voice UX; smart/expensive text model for reasoning. The realtime model calls a single tool that proxies to the text supervisor, which runs its own tool loop server-side before returning a final answer.

8. **State-machine prompting** (customerServiceRetail scenario) — Complex multi-step flows (e.g., authentication) are encoded as explicit states in the system prompt with transition instructions.

9. **Codec negotiation** — SDP-level codec preference injection via `changePeerConnection` hook allows narrow-band audio simulation for telephony testing, without any application-layer changes.
