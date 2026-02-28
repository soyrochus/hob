## Context

Phase 1 introduced a static avatar panel in user mode and preserved debug mode behavior. This Phase 2 change adds speech-reactive overlays driven by the existing SDK audio element so the avatar visibly responds to AI output in real time, without changing session, transcript, or agent orchestration architecture.

Current constraints:
- Keep existing user/debug mode contract unchanged.
- Keep phase scope limited to overlay reactivity (no unrelated UI redesign).
- Use browser-native Web Audio APIs with no new external dependencies.
- Overlay assets are bundled in `public/avatars/overlays/`.

## Goals / Non-Goals

**Goals:**
- Add an audio-level hook that converts AI output amplitude into discrete levels `0..4`.
- Update `Avatar` to layer overlay frames over base image using those levels.
- Ensure level `0` renders no overlay; levels `1..4` map to `overlay-1..4`.
- Pass `sdkAudioElement` from `App.tsx` to `Avatar` as the audio source.
- Preserve existing mode behavior: user mode uses `Avatar`; debug mode uses `Events`.

**Non-Goals:**
- No changes to top navbar behavior or debug/user mode toggling behavior.
- No backend/API route changes.
- No animated GIF/WebP playback pipeline; frame changes are driven by level updates.
- No additional visual effects beyond overlay frame selection.

## Decisions

### 1. Audio analysis lives in `useAvatarAudioLevel`

Decision:
- Create `src/app/hooks/useAvatarAudioLevel.ts` that owns `AudioContext`, `MediaElementSource`, `AnalyserNode`, and frame loop lifecycle.

Rationale:
- Encapsulates a complex browser API behind a stable hook API and keeps `Avatar` focused on presentation.

Alternatives considered:
- Keeping `AudioContext` in `App.tsx` and passing analysis state down was rejected because it broadens app-level state surface and couples unrelated concerns.

### 2. Discrete threshold mapping from RMS to level

Decision:
- Compute RMS from time-domain analyser data and map to levels with configurable thresholds:
  - `0.00–0.01 => 0`
  - `0.01–0.10 => 1`
  - `0.10–0.25 => 2`
  - `0.25–0.50 => 3`
  - `0.50+ => 4`

Rationale:
- Discrete levels directly match provided overlay asset set and reduce visual jitter compared to continuous values.

Alternatives considered:
- Frequency-domain energy mapping was rejected for initial phase because RMS on time-domain samples is simpler and sufficient for visible responsiveness.

### 3. Overlay rendering remains declarative in `Avatar`

Decision:
- `Avatar` accepts `audioElement`, calls `useAvatarAudioLevel(audioElement)`, resolves overlay path from config/defaults, and conditionally renders overlay layer only when `level > 0`.

Rationale:
- Keeps existing base-image path intact and introduces minimal structural changes.

Alternatives considered:
- CSS-only effects without assets were rejected because the requirement is explicit frame asset usage (`overlay-1..4`).

### 4. Safe media-element source initialization

Decision:
- Guard hook initialization with refs and effect cleanup to avoid duplicate `createMediaElementSource` attachment and prevent resource leaks on unmount/reconnect.

Rationale:
- Web Audio media-element source creation is sensitive to repeated binding; explicit guards avoid runtime exceptions.

Alternatives considered:
- Recreating `AudioContext` each render was rejected due to instability and unnecessary overhead.

## Risks / Trade-offs

- [Risk] Overlay flicker or unstable level transitions in noisy audio segments.
  → Mitigation: update state only on level changes and optionally throttle updates (e.g., every 2–3 animation frames).

- [Risk] Browser autoplay/audio-context restrictions can delay analyser start.
  → Mitigation: lazy-init when `audioElement` exists and tolerate temporary level `0` until audio is active.

- [Risk] Missing overlay assets lead to broken image requests.
  → Mitigation: define default overlay paths in config and allow null-safe overlay rendering.

- [Risk] Additional per-frame work affects UI performance on low-end devices.
  → Mitigation: use small analyser buffer and minimal math; avoid unnecessary re-renders.

## Migration Plan

1. Add overlay assets under `public/avatars/overlays/overlay-{1..4}.png`.
2. Add `useAvatarAudioLevel` hook with analyser lifecycle and level mapping.
3. Update avatar config defaults/override usage for overlay paths.
4. Update `Avatar` props and rendering to include audio-reactive overlay layering.
5. Pass `sdkAudioElement` into `Avatar` from `App.tsx`.
6. Validate behavior in user mode during active AI speech and silence.

Rollback:
- Remove `audioElement` prop flow and hook usage from `Avatar`.
- Revert `Avatar` to base-image-only rendering.
- Leave existing mode toggle/panel routing untouched.

## Open Questions

- Should threshold values be environment-tuned per voice model, or remain global?
- Should overlay fallback behavior be explicit (`no overlay`) if a specific level asset is missing?
