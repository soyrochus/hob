# Architecture Baseline — Hob

> **Status**: Baseline documentation of the application as it currently stands, before Hob-specific modifications.
>
> This application is a fork of [OpenAI's Realtime API Agents Demo](https://github.com/openai/openai-realtime-agents), used under the MIT license and being adapted into a new product called **Hob**.

---

## 1. Overview

Hob is a **voice-first multi-agent application** built on the OpenAI Realtime API. It enables low-latency, streaming voice conversations with AI agents that can call tools, hand off between each other, and be supervised by higher-intelligence text-based models. The current codebase contains three functional demo scenarios that showcase different agent architecture patterns.

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15.3.1 (App Router) |
| Language | TypeScript (strict mode) |
| UI | React 19, Tailwind CSS |
| Agent Orchestration | `@openai/agents` v0.0.5 (OpenAI Agents SDK) |
| Voice Transport | WebRTC via OpenAI Realtime API |
| Text Intelligence | OpenAI Responses API (gpt-4.1, gpt-4o-mini) |
| Schema Validation | Zod |
| State Management | React Context API |

---

## 2. Top-Level Project Structure

```
/
├── src/
│   └── app/
│       ├── App.tsx                  # Root client component
│       ├── page.tsx                 # Next.js page; wraps App in context providers
│       ├── layout.tsx               # Root HTML layout
│       ├── types.ts                 # Core TypeScript enums and interfaces
│       ├── api/
│       │   ├── session/route.ts     # Creates ephemeral OpenAI Realtime sessions
│       │   └── responses/route.ts   # Proxy to OpenAI Responses API
│       ├── agentConfigs/            # All agent scenario definitions
│       ├── components/              # React UI components
│       ├── contexts/                # React Context providers
│       ├── hooks/                   # Custom React hooks
│       └── lib/                    # Utility functions
├── docs/                            # Documentation (this file lives here)
├── ORIG_OPENAI_README.md            # Original OpenAI demo README
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

1. The browser calls `GET /api/session`, which forwards to OpenAI and returns a short-lived ephemeral key (1 hour TTL).
2. The browser uses that key to establish a **WebRTC peer connection** directly with OpenAI's Realtime API — audio is end-to-end encrypted and does not pass through the Next.js server.
3. All subsequent intelligence (agent responses, tool calls, handoffs) streams back over the same WebRTC connection.

### 3.2 Supervisor (Text API) Flow

For scenarios where more intelligence is needed than a realtime model provides, the chatSupervisor pattern routes requests through a second path:

```
Browser                     Next.js Server              OpenAI
  │                               │                        │
  │── POST /api/responses ───────>│                        │
  │   { messages, tools }         │── Responses API ──────>│
  │                               │   (gpt-4.1, tool loop) │
  │                               │<── text response ───────│
  │<── { output } ───────────────│                        │
```

This endpoint proxies to the OpenAI Responses API and handles iterative tool-call loops server-side before returning the final text.

---

## 4. Agent Architecture

### 4.1 Agent Definition Model

All agents are instances of `RealtimeAgent` from the OpenAI Agents SDK. An agent is defined by:

```typescript
{
  name: string,                  // Unique identifier
  voice: string,                 // TTS voice selection (e.g. "sage")
  instructions: string,          // System prompt / persona
  tools: tool[],                 // Callable functions
  handoffs: RealtimeAgent[],     // Agents this agent can transfer to
  handoffDescription: string,    // Description shown to other agents when routing
}
```

### 4.2 The Three Demo Scenarios

The application ships with three distinct agent configurations, selectable via URL param (`?agentConfig=`) or a UI dropdown.

---

#### Scenario A: Simple Handoff (`simpleHandoff`)

The minimal reference implementation of agent-to-agent transfer.

```
greeterAgent ──handoff──> haikuWriterAgent
```

- `greeterAgent` introduces itself and asks if the user wants a haiku.
- On confirmation, it invokes a handoff, transferring the conversation to `haikuWriterAgent`.
- Demonstrates the core one-way handoff primitive.

---

#### Scenario B: Chat Supervisor (`chatSupervisor`)

A two-tier architecture that separates fast interaction from deep reasoning.

```
         User (voice)
              │
       ┌──────▼──────┐
       │  Chat Agent  │   gpt-4o-realtime-mini
       │  (realtime)  │   Low latency, voice output
       └──────┬───────┘
              │ tool call: getNextResponseFromSupervisor()
              │
         POST /api/responses
              │
       ┌──────▼──────┐
       │  Supervisor  │   gpt-4.1 (text model)
       │   Agent      │   High intelligence, tool execution
       └──────┬───────┘
              │ tools
       ┌──────┴────────────────┐
       │                       │
  lookupPolicy          getUserAccountInfo
  Document()            findNearestStore()
```

**Design rationale:**
- The realtime mini model handles greetings, fillers, and simple questions directly — low cost and low latency.
- Complex or policy-sensitive questions are forwarded (with full conversation history) to the text-based supervisor model, which can call tools iteratively and return a precise answer.
- The chat agent reads the supervisor's response verbatim to the user.
- Tool data is currently served from mock data (`sampleData.ts`).

---

#### Scenario C: Customer Service Retail (`customerServiceRetail`)

A fully-connected multi-agent network for a fictional snowboard retailer ("Snowy Peak Boards").

```
      ┌───────────────────────────────────────┐
      │                                       │
 authentication ──────> returns <──────> sales
      │                    │                  │
      └──────────────> simulatedHuman <───────┘
```

All agents in this network can hand off to each other (bidirectional), with the exception of `authentication`, which is always the entry point.

| Agent | Responsibility | Notable Tools |
|-------|---------------|---------------|
| `authentication` | Verifies user identity via a state-machine prompt | — |
| `returns` | Order lookup, return eligibility, initiates returns | `lookupOrders`, `retrievePolicy`, `checkEligibilityAndPossiblyInitiateReturn` |
| `sales` | Product recommendations, promotions, checkout | `lookupNewSales`, `addToCart`, `checkout` |
| `simulatedHuman` | Escalation endpoint; represents a human representative | — |

The `returns` agent calls `o4-mini` for high-stakes eligibility decisions (a second-tier reasoning pattern within a single agent).

---

### 4.3 Tool Execution

Tools are defined with a Zod-compatible JSON schema and an `execute` function:

```
Agent generates text ──> SDK intercepts function_call
                              │
                         execute() runs locally
                              │
                         Result injected back into conversation
                              │
                         Agent continues
```

Tools execute **in the browser process** for realtime agents, or **on the server** (via `/api/responses`) for supervisor agents.

---

## 5. Voice & Audio System

### 5.1 Transport

- Audio uses **WebRTC** (`RTCPeerConnection`) via `OpenAIRealtimeWebRTC` from the SDK.
- Remote audio is rendered through a hidden `<audio>` element injected into the DOM.
- Codec negotiation is configurable: **opus 48kHz** (default, high quality) or **PCMU/PCMA 8kHz** (narrow-band, PSTN simulation).

### 5.2 Voice Activity Detection (VAD)

The default mode uses server-side VAD, configured with:

| Parameter | Value |
|-----------|-------|
| Threshold | 0.9 |
| Prefix padding | 300 ms |
| Silence duration | 500 ms |

An alternative **Push-to-Talk (PTT)** mode is available via a UI toggle, replacing VAD with explicit button-hold interaction.

### 5.3 Transcription

User speech is transcribed by `gpt-4o-mini-transcribe`. Transcription deltas stream in real time and are accumulated into the transcript UI. Unparseable audio falls back to `[inaudible]`.

### 5.4 Audio Recording & Download

The application can record the full conversation (both sides) by:
1. Merging the microphone stream and the remote audio stream via the Web Audio API (`AudioContext`).
2. Recording as WebM with `MediaRecorder`.
3. Converting the WebM blob to WAV on download via `audioUtils.ts`.

---

## 6. State Management

### 6.1 Context Providers

State is managed via two React Context providers, both mounted at the `page.tsx` level.

**TranscriptContext** — owns the conversation UI model:

| Item type | Description |
|-----------|-------------|
| `MESSAGE` | A user or assistant utterance, with streaming-safe delta updates |
| `BREADCRUMB` | A metadata annotation (tool call, handoff, guardrail event) |

Key operations: `addTranscriptMessage`, `updateTranscriptMessage`, `addTranscriptBreadcrumb`, `toggleExpand`, `updateTranscriptItem`.

**EventContext** — owns the developer event log:
- Logs all SDK events with direction (`⬆` client-originated, `⬇` server-originated).
- Each entry is expandable to its raw JSON payload.
- Used exclusively by the `Events.tsx` debug panel.

### 6.2 Session State (local to App.tsx)

| State variable | Type | Purpose |
|----------------|------|---------|
| `sessionStatus` | `DISCONNECTED \| CONNECTING \| CONNECTED` | Connection lifecycle |
| `selectedAgentConfigSet` | `RealtimeAgent[]` | Active agent scenario |
| `selectedAgentName` | `string` | Currently active agent in session |
| `isPTTActive` | `boolean` | PTT mode enabled |
| `isPTTUserSpeaking` | `boolean` | User holding PTT button |

### 6.3 Persistent Preferences (localStorage)

| Key | Stored value |
|-----|-------------|
| `pushToTalkUI` | PTT mode preference |
| `logsExpanded` | Event panel open/closed |
| `audioPlaybackEnabled` | Speaker output on/off |

---

## 7. Output Guardrails

Every assistant message is passed asynchronously through a moderation step powered by `gpt-4o-mini`:

```
Assistant message completes
        │
  POST /api/responses (guardrail prompt)
        │
  gpt-4o-mini classifies text
        │
  ┌─────┴─────────────────────┐
  │ NONE   OFFENSIVE   OFF_BRAND   VIOLENCE │
  └─────┬─────────────────────┘
        │
  Result stored in transcript item
        │
  GuardrailChip UI updates (pending → pass/fail)
        │
  If triggered: corrective message injected into conversation
```

The moderation prompt is parameterized by `companyName` for brand-specific customization.

---

## 8. UI Layer

### 8.1 Layout

```
┌─────────────────────────────────────────────────┐
│  [Scenario ▼]  [Agent ▼]                        │  ← Top bar
├──────────────────────────┬──────────────────────┤
│                          │                      │
│      Transcript          │     Events Log       │
│   (messages + crumbs)    │  (SDK event stream)  │
│                          │                      │
├──────────────────────────┴──────────────────────┤
│  [Connect/Disconnect]  [PTT □]  [🔊]  [Codec ▼] │  ← Bottom toolbar
└─────────────────────────────────────────────────┘
```

### 8.2 Components

| Component | File | Responsibility |
|-----------|------|---------------|
| `App` | `App.tsx` | Root layout, session orchestration, event wiring |
| `Transcript` | `Transcript.tsx` | Message bubbles, breadcrumbs, text input, auto-scroll |
| `Events` | `Events.tsx` | Collapsible raw event log with JSON drill-down |
| `BottomToolbar` | `BottomToolbar.tsx` | Connection controls, PTT, audio, codec selector |
| `GuardrailChip` | `GuardrailChip.tsx` | Inline moderation status per message |

---

## 9. Key Hooks

| Hook | File | Responsibility |
|------|------|---------------|
| `useRealtimeSession` | `hooks/useRealtimeSession.ts` | Manages the SDK `RealtimeSession`; handles connect/disconnect, audio element creation, codec negotiation, PTT events |
| `useHandleSessionHistory` | `hooks/useHandleSessionHistory.ts` | Subscribes to SDK history events and translates them into context updates (transcript items, breadcrumbs, event log entries) |
| `useAudioDownload` | `hooks/useAudioDownload.ts` | Merges and records audio streams; exposes download handler |

---

## 10. API Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/session` | GET | Creates an OpenAI Realtime session and returns the ephemeral client secret |
| `/api/responses` | POST | Proxies to the OpenAI Responses API; runs iterative tool-call loops for supervisor and guardrail calls |

Both routes require `OPENAI_API_KEY` in the environment.

---

## 11. Data Flow Summary

### Voice input → transcript

```
Microphone → WebRTC → OpenAI VAD → transcription deltas
                                        → handleTranscriptionDelta()
                                        → TranscriptContext (MESSAGE, streaming)
```

### Agent response → audio + transcript

```
OpenAI generates response → audio stream → <audio> element → speaker
                         → transcript delta → TranscriptContext (MESSAGE, streaming)
                         → [guardrail check] → GuardrailChip
```

### Tool call

```
Agent emits function_call → SDK captures → tool.execute() runs
                                         → result injected into history
                                         → EventContext (breadcrumb)
                                         → agent continues
```

### Agent handoff

```
Agent calls transfer_to_{agent} → SDK routes session to new agent
                                → EventContext (breadcrumb: "handoff")
                                → App.tsx updates selectedAgentName
```

---

## 12. Configuration & Build

- **TypeScript**: strict mode, target ES2017, path alias `@/*` → `./src/*`
- **Tailwind CSS**: utility classes, no custom theme configuration
- **Environment variable**: `OPENAI_API_KEY` (required)
- **Dev server**: `npm run dev` (Next.js on port 3000)
- **Agent scenario selection**: URL parameter `?agentConfig=<key>` or UI dropdown

### Agent Registry

Scenarios are registered in `src/app/agentConfigs/index.ts`:

```typescript
const allAgentSets = {
  simpleHandoff,          // Basic 2-agent handoff demo
  customerServiceRetail,  // Multi-agent retail customer service
  chatSupervisor,         // Two-tier realtime + text supervisor
};
const defaultAgentSetKey = 'chatSupervisor';
```

Adding a new scenario requires: creating a file exporting a `RealtimeAgent[]` array, then registering it in this map.

---

## 13. Notable Design Patterns

1. **Two-tier agent architecture** — cheap/fast realtime model for voice UX, expensive/smart text model for reasoning. Reduces cost and latency simultaneously.
2. **Supervisor tool iteration loop** — the `/api/responses` route runs tools in a loop until the model produces a final text response, server-side, before returning to the client.
3. **Breadcrumb pattern** — non-speech events (tool calls, handoffs, guardrail results) are embedded as collapsible metadata items in the transcript stream rather than in a separate log.
4. **State-machine prompting** — complex multi-step flows (e.g., authentication) are encoded as explicit states in the system prompt, with instructions for each transition.
5. **Async guardrails** — moderation runs after response completion and does not block audio playback; UI updates asynchronously.
6. **Codec negotiation** — SDP-level codec preference injection allows the same app to simulate PSTN-quality narrow-band audio for telephony testing.
