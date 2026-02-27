# Hob

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)[![FOSS Pluralism](https://img.shields.io/badge/FOSS-Pluralism-green.svg)](FOSS_PLURALISM_MANIFESTO.md)

[![OpenAI Realtime API](https://img.shields.io/badge/OpenAI-Realtime%20API-412991?logo=openai&logoColor=white)](https://platform.openai.com/docs/guides/realtime)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)

> *Talk. Delegate. Done.*

**Hob** is a voice-first, multi-agent application built on the [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime). It supports low-latency streaming voice conversations with AI agents that can call tools, hand off between each other, and delegate complex reasoning to higher-intelligence text models — all in real time.

Hob is a fork of [OpenAI's Realtime API Agents Demo](https://github.com/openai/openai-realtime-agents), used under the MIT license and being developed into a new product in the open.

![Hob](images/Hob-small.png)

## Getting Started

### Prerequisites

- Node.js 18+
- An [OpenAI API key](https://platform.openai.com/api-keys) with Realtime API access

### Installation

```bash
npm install
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
```

### Running

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. Click **Connect** to start a voice session.

---

## How It Works

Hob uses **WebRTC** to stream audio directly between the browser and the OpenAI Realtime API — the Next.js server is only involved in minting a short-lived session token. Once connected, the conversation is handled by a network of AI agents defined in `src/app/agentConfigs/`.

Three demo scenarios are included:

| Scenario | Description |
| -------- | ----------- |
| `chatSupervisor` *(default)* | A fast realtime model handles voice; a smarter text model handles complex queries and tool calls behind the scenes |
| `customerServiceRetail` | A fully-connected network of four agents for a fictional snowboard retailer — authentication, returns, sales, and human escalation |
| `simpleHandoff` | Minimal two-agent handoff reference implementation |

Select a scenario from the dropdown in the top bar, or pass `?agentConfig=<name>` as a URL parameter.

### Key Features

- **Voice or Push-to-Talk** — server-side VAD by default; PTT mode available via the toolbar
- **Multi-agent handoffs** — agents transfer the conversation context to each other seamlessly
- **Tool calling** — agents can look up data, manage carts, check policies, and more
- **Output guardrails** — every response is asynchronously checked for offensive, off-brand, or violent content
- **Audio recording** — the full conversation (both sides) can be downloaded as a WAV file
- **Developer event log** — a live panel shows every SDK and API event with expandable JSON payloads

---

## Architecture

For a full description of the system design, see [docs/hob-architecture-baseline.md](docs/hob-architecture-baseline.md).

High-level stack: **Next.js 15** · **React 19** · **TypeScript** · **OpenAI Agents SDK** · **WebRTC** · **Tailwind CSS**

## Principles of Participation

Everyone is invited and welcome to contribute: open issues, propose pull requests, share ideas, or help improve documentation.  
Participation is open to all, regardless of background or viewpoint.  

This project follows the [FOSS Pluralism Manifesto](./FOSS_PLURALISM_MANIFESTO.md),  
which affirms respect for people, freedom to critique ideas, and space for diverse perspectives.  


## License and Copyright

Copyright (c) 2025, 2026 OpenAI, Iwan van der Kleijn

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
