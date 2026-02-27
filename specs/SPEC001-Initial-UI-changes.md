# UI Changes: Debug Mode Toggle

## Goal

Add a persistent **Debug toggle** (a small slider/switch) to the bottom-right of the UI.
It controls two modes:

| Mode | Default? | Right panel | Footer controls |
|---|---|---|---|
| **User mode** (debug OFF) | Yes | `Avatar.tsx` | Hidden |
| **Debug mode** (debug ON) | No | `Events.tsx` (current Logs panel) | All visible |

The Debug toggle itself is **always visible** in both modes.

---

## Current Layout (reference)

```
┌─────────────────────────────────────────────────────────────┐
│  Top navbar (logo, Scenario selector, Agent selector)       │
├─────────────────────────────┬───────────────────────────────┤
│                             │                               │
│   Transcript.tsx            │   Events.tsx                  │
│   (flex-1)                  │   (w-1/2 when expanded,       │
│                             │    w-0 when collapsed)        │
│                             │                               │
├─────────────────────────────┴───────────────────────────────┤
│  BottomToolbar: [Connect] [PTT] [Audio] [Logs] [Codec]      │
└─────────────────────────────────────────────────────────────┘
```

After the change:

```
┌─────────────────────────────────────────────────────────────┐
│  Top navbar (unchanged)                                     │
├─────────────────────────────┬───────────────────────────────┤
│                             │                               │
│   Transcript.tsx            │   Avatar.tsx  (user mode)     │
│   (flex-1, unchanged)       │  ─── OR ───                   │
│                             │   Events.tsx  (debug mode)    │
│                             │                               │
├─────────────────────────────┴───────────────────────────────┤
│  [hidden in user mode]                      [Debug ●──○]    │
└─────────────────────────────────────────────────────────────┘
```

---

## State: `isDebugMode`

A single new boolean drives all the changes.

- **Location**: `App.tsx` — alongside the existing `isEventsPaneExpanded` state.
- **Default**: `false` (user mode).
- **Persistence**: `localStorage` key `"debugMode"`, loaded in the existing `useEffect` that
  restores other UI preferences (around line 353).

```ts
const [isDebugMode, setIsDebugMode] = useState<boolean>(false);
// in the localStorage restore effect:
const storedDebugMode = localStorage.getItem("debugMode");
if (storedDebugMode) setIsDebugMode(storedDebugMode === "true");
// in its own persistence effect:
useEffect(() => { localStorage.setItem("debugMode", isDebugMode.toString()); }, [isDebugMode]);
```

---

## Change 1 — `App.tsx`: right panel conditional render

In the main `flex` area (currently lines 518–530), replace the unconditional `<Events />` with a
conditional:

```tsx
{/* Right panel */}
{isDebugMode
  ? <Events isExpanded={isEventsPaneExpanded} />
  : <Avatar />                         // always w-1/2, always visible in user mode
}
```

`Avatar` should occupy a fixed `w-1/2` regardless of the `isEventsPaneExpanded` toggle (that
toggle only matters inside debug mode).

Also pass the new props to `<BottomToolbar>`:

```tsx
<BottomToolbar
  ...existing props...
  isDebugMode={isDebugMode}
  setIsDebugMode={setIsDebugMode}
/>
```

---

## Change 2 — `BottomToolbar.tsx`: hide controls in user mode

Add two new props: `isDebugMode: boolean` and `setIsDebugMode: (val: boolean) => void`.

Wrap all existing controls (Connect, PTT, Audio, Logs, Codec) in a conditional that renders them
`invisible` (not `hidden` — so the bar height stays constant) when `!isDebugMode`:

```tsx
<div className={`flex flex-row items-center gap-x-8 ${!isDebugMode ? "invisible" : ""}`}>
  {/* Connect button */}
  {/* Push-to-talk */}
  {/* Audio playback */}
  {/* Logs checkbox */}
  {/* Codec selector */}
</div>
```

Then add the Debug toggle to the right, **outside** that wrapper so it is always visible:

```tsx
<div className="flex flex-row items-center gap-2 ml-auto">
  <label htmlFor="debug-mode" className="text-sm text-gray-500 cursor-pointer">
    Debug
  </label>
  {/* Toggle slider — see styling note below */}
  <input
    id="debug-mode"
    type="checkbox"
    role="switch"
    checked={isDebugMode}
    onChange={(e) => setIsDebugMode(e.target.checked)}
  />
</div>
```

**Styling the slider**: Use a CSS toggle-switch pattern (a styled `<label>` wrapping a hidden
`<input type="checkbox">`), or a small Tailwind peer-class trick.  A simple, self-contained
option is to add a `DebugToggle.tsx` sub-component that encapsulates the pill-shaped slider so
`BottomToolbar` stays clean.

---

## Change 3 — Create `Avatar.tsx`

New file: `src/app/components/Avatar.tsx`

See the full visual and behavioural specification in the sections below.
Implementation is **phased** — see Phased Implementation Plan.

---

## Avatar: Visual Design

The Avatar panel is a layered image composition. At any moment it shows:

```
┌─────────────────────────────────┐
│         Avatar panel            │
│   (w-1/2, full height,          │
│    white bg, rounded-xl)        │
│                                 │
│   ┌───────────────────────┐     │
│   │   base image          │     │  ← always visible, configurable per agent
│   │  (centred, fixed size)│     │
│   │                       │     │
│   │  [overlay image]      │     │  ← transparent PNG, superimposed on base
│   │  (same size, absolute)│     │    level 0 = no overlay
│   └───────────────────────┘     │  level 1–4 = one of four overlay PNGs
│                                 │
└─────────────────────────────────┘
```

### Base image

- A single static image representing the agent's persona.
- Configurable per agent (see Agent Config section below).
- Falls back to a default placeholder if not configured.
- Rendered as a centred `<img>` (or Next.js `<Image>`) inside the panel.

### Overlay images — 5 states

| Sound level | Overlay shown |
|---|---|
| 0 — silence / below threshold | no overlay (transparent / null) |
| 1 — low | `overlay-1.png` |
| 2 — medium-low | `overlay-2.png` |
| 3 — medium-high | `overlay-3.png` |
| 4 — high | `overlay-4.png` |

The four overlay PNGs:

- Same pixel dimensions as the base image.
- **Transparent background** — only the graphic effect is opaque.
- Contain a "marquee" graphic (e.g. a glowing ring, pulsing halo, or animated border
  baked into the PNG) that emphasises speech intensity.
- Swapping between them as the level changes produces the visual blinking/pulse effect.
- Bundled with the app (not fetched at runtime) — placed in `public/avatars/overlays/`.
- Also configurable per agent (can override the defaults).

### Layering in CSS

```
position: relative   ← wrapper div, fixed size
  <img base />       ← position: static, full width/height
  <img overlay />    ← position: absolute, inset: 0, same size
                        opacity: 0 when level === 0
```

No CSS animations on the component itself. The "blinking" emerges naturally from React
re-rendering as `soundLevel` changes (typically every ~50–100 ms in the audio poll loop).

---

## Avatar: Agent Config Integration

`RealtimeAgent` (from the SDK) cannot carry arbitrary metadata. The solution is a **parallel
config map** keyed by agent name, separate from the agent array.

### New type — `AvatarConfig`

New file: `src/app/agentConfigs/avatarConfig.ts`

```ts
export interface AvatarConfig {
  /** Path to the base image, relative to /public  */
  baseImage: string;
  /** Optional per-agent overlay images. Falls back to app defaults if omitted. */
  overlayImages?: {
    level1: string;
    level2: string;
    level3: string;
    level4: string;
  };
}

/** Default overlay paths used when an agent doesn't specify its own */
export const defaultOverlays = {
  level1: "/avatars/overlays/overlay-1.png",
  level2: "/avatars/overlays/overlay-2.png",
  level3: "/avatars/overlays/overlay-3.png",
  level4: "/avatars/overlays/overlay-4.png",
};

/** Default base image used when an agent doesn't specify one */
export const defaultBaseImage = "/avatars/default-avatar.png";

/** Map from agent name → avatar config */
export const avatarConfigs: Record<string, AvatarConfig> = {
  // populated per scenario, e.g.:
  // chatAgent: { baseImage: "/avatars/chat-agent.png" },
  // authenticationAgent: { baseImage: "/avatars/auth-agent.png" },
};
```

Each scenario's own `index.ts` can add entries to `avatarConfigs` at module load time,
keeping the avatar configuration co-located with the agent definition.

### How `App.tsx` passes it to `Avatar`

`App.tsx` already knows `selectedAgentName`. It looks up the config and passes it down:

```tsx
import { avatarConfigs, defaultBaseImage, defaultOverlays } from "@/app/agentConfigs/avatarConfig";

const avatarConfig = avatarConfigs[selectedAgentName] ?? { baseImage: defaultBaseImage };

// In JSX:
<Avatar
  config={avatarConfig}
  audioElement={sdkAudioElement}   // needed for Phase 2 sound detection
/>
```

---

## Avatar: Sound Level Detection (Phase 2)

The AI audio comes through `sdkAudioElement` (the `<audio>` element created in `App.tsx`
that plays the Realtime stream). Sound level is measured using the **Web Audio API**.

### Hook — `useAvatarAudioLevel`

New file: `src/app/hooks/useAvatarAudioLevel.ts`

```ts
// Signature
function useAvatarAudioLevel(
  audioElement: HTMLAudioElement | null | undefined
): 0 | 1 | 2 | 3 | 4
```

Internal approach:

1. On mount (or when `audioElement` becomes non-null), create an `AudioContext` and wire:
   `createMediaElementSource(audioElement)` → `createAnalyser()` → `destination`
2. Start a `requestAnimationFrame` loop that calls `analyser.getByteTimeDomainData(buffer)`
   each frame and computes an RMS (root mean square) amplitude value in 0–1.
3. Map the RMS to a discrete level:
   - 0.00–0.01 → level 0 (silence threshold)
   - 0.01–0.10 → level 1
   - 0.10–0.25 → level 2
   - 0.25–0.50 → level 3
   - 0.50–1.00 → level 4
   *(thresholds to be tuned after testing)*
4. Store as React state — update triggers Avatar re-render → overlay swap.
5. Cancel the animation frame and close the `AudioContext` on unmount.

**Important**: `createMediaElementSource` can only be called once per element per
`AudioContext`. The hook must guard against double-initialisation (use a ref flag).

The poll rate of `requestAnimationFrame` (~60 fps) is faster than necessary; the hook can
throttle updates to every 2–3 frames to reduce re-renders without noticeable lag.

---

## Phased Implementation Plan

### Phase 1 — Static Avatar component

**Goal**: A working `Avatar.tsx` that shows the correct base image for the active agent.
No sound detection, no overlays, no animation.

**Deliverables**:

1. `src/app/agentConfigs/avatarConfig.ts` — type, defaults, empty map.
2. `src/app/components/Avatar.tsx` — renders base image (or a grey placeholder if no image
   configured), correct panel dimensions, `rounded-xl` style.
3. `App.tsx` — look up `avatarConfig`, pass `config` prop to `Avatar`.
4. At least one scenario (e.g. `chatSupervisor`) has an entry in `avatarConfigs` with a
   real or placeholder image to verify the config pipeline end-to-end.

**Done when**: User mode shows the panel with the agent's base image; switching agents updates
the image; debug mode still shows `Events.tsx` unchanged.

---

### Phase 2 — Sound-reactive overlay animation

**Goal**: The overlay images respond to the AI's actual audio output in real time.

**Deliverables**:

1. `public/avatars/overlays/overlay-1.png` through `overlay-4.png` — the four overlay assets
   (created by designer; transparent background, marquee/glow effect).
2. `src/app/hooks/useAvatarAudioLevel.ts` — the Web Audio API hook.
3. `Avatar.tsx` updated to:
   - Accept `audioElement` prop.
   - Call `useAvatarAudioLevel(audioElement)` to get `soundLevel`.
   - Render the appropriate overlay (or nothing at level 0) stacked over the base image.
4. `App.tsx` passes `audioElement={sdkAudioElement}` to `<Avatar>`.

**Done when**: In user mode, the overlay image visibly changes as the AI speaks, with no
overlay shown during silence.

---

## Files to Touch

| File | Phase | Change |
| --- | --- | --- |
| `src/app/App.tsx` | 1 | Add `isDebugMode` state + localStorage; conditional right-panel render; look up `avatarConfig`; pass props to `BottomToolbar` and `Avatar` |
| `src/app/components/BottomToolbar.tsx` | 1 | Add `isDebugMode`/`setIsDebugMode` props; hide controls in user mode; add Debug toggle |
| `src/app/components/Avatar.tsx` | 1 | **New** — base image display, correct panel dimensions |
| `src/app/agentConfigs/avatarConfig.ts` | 1 | **New** — `AvatarConfig` type, default paths, `avatarConfigs` map |
| (optional) `src/app/components/DebugToggle.tsx` | 1 | **New** — self-contained pill-slider widget |
| `src/app/hooks/useAvatarAudioLevel.ts` | 2 | **New** — Web Audio API analyser hook |
| `public/avatars/overlays/overlay-{1-4}.png` | 2 | **New** — overlay image assets |
| `public/avatars/default-avatar.png` | 1 | **New** — default base image asset |

No changes needed to `Events.tsx`, `Transcript.tsx`, contexts, or agent logic.

---

## Open Questions (to resolve before implementing)

1. **Top navbar in user mode**: Should the Scenario/Agent selectors also be hidden, or only
   the footer controls?
2. **`isEventsPaneExpanded` in user mode**: When returning to debug mode, should the Events
   pane remember its last expanded/collapsed state? (Proposal: yes — leave state untouched.)
3. **Debug toggle visual style**: Plain checkbox, pill slider, or icon button (e.g. a `bug`
   icon that toggles active/inactive)?
4. **Overlay asset format**: Should the overlays be static PNGs (blinking effect from
   React swapping), or animated GIFs/WebP (effect baked into the file itself)?
5. **Audio level thresholds**: The RMS→level mapping values need tuning against real
   `gpt-4o-realtime` audio output — to be calibrated during Phase 2 testing.
6. **`AudioContext` lifecycle**: `sdkAudioElement` is created once in `App.tsx`. Should
   the `AudioContext` live in `App.tsx` (created once) and be passed down, or be owned
   entirely inside the `useAvatarAudioLevel` hook?
