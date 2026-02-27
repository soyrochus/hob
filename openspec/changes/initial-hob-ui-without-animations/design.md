## Context

The baseline Hob UI is debug-oriented: the right panel is `Events`, and footer controls are always visible. This change introduces a product-facing user mode while retaining a developer/debug mode. The architecture remains a Next.js client UI around existing Realtime session hooks and agent config selection.

Key constraints:
- Preserve existing session, transcript, and event plumbing.
- Add no new runtime dependencies.
- Exclude Phase 2 sound-reactive overlay behavior and UI animations.
- Keep intentional baseline deviation explicit: user mode prioritizes avatar-first presentation over always-visible debug controls.

## Goals / Non-Goals

**Goals:**
- Guarantee exactly two UI modes are supported: `user` and `debug`.
- Guarantee mode switching is always possible from the UI via a persistent, always-visible Debug toggle.
- Default to user mode (`isDebugMode = false`) with `localStorage` persistence (`debugMode`).
- Show `Avatar` in user mode and `Events` in debug mode using one app-level source of truth.
- Keep toolbar height and layout stable when debug controls are hidden in user mode.
- Support per-agent avatar base image configuration with safe fallback behavior.

**Non-Goals:**
- No sound-level detection hook integration in this phase.
- No overlay-frame swapping, pulse effects, or animation behavior.
- No changes to API routes, session transport, guardrail pipeline, or agent execution model.

## Decisions

### 1. Single source of truth for mode in `App.tsx`

Decision:
- Add `isDebugMode` state in `App.tsx` and persist via `localStorage`.

Rationale:
- `App.tsx` already orchestrates global UI state (`selectedAgentName`, pane visibility, audio/session controls). Keeping mode state there prevents cross-component divergence.

Alternatives considered:
- React Context for mode: rejected as unnecessary for current scope and broader than needed.
- Local state in `BottomToolbar`: rejected because `App` needs mode for right-panel render decisions.

### 2. Explicit two-mode rendering contract

Decision:
- Right panel rendering is mode-gated:
  - `isDebugMode === false` => render `Avatar`
  - `isDebugMode === true` => render `Events`

Rationale:
- Encodes the guarantee directly into render logic and avoids ambiguous intermediate states.

Alternatives considered:
- Rendering both panels and toggling visibility with CSS: rejected due to unnecessary work and complexity.

### 3. Toolbar split: debug controls vs always-on mode switch

Decision:
- Wrap existing controls (`Connect`, `PTT`, `Audio`, `Logs`, `Codec`) in a container that becomes `invisible` in user mode.
- Place Debug toggle outside that wrapper so it is always visible.

Rationale:
- Ensures mode switching is always accessible while preserving toolbar dimensions.

Alternatives considered:
- Use `hidden` for debug controls: rejected because it changes layout height/spacing.
- Keep connect controls visible in user mode: rejected for this phase to maintain a clean consumer-facing user mode.

### 4. Avatar config as sidecar map keyed by agent name

Decision:
- Add `src/app/agentConfigs/avatarConfig.ts` with `avatarConfigs`, `defaultBaseImage`, and default overlay paths for later phases.

Rationale:
- `RealtimeAgent` type should remain unchanged; sidecar config avoids mutating SDK-owned shapes.
- Keeps scenario/avatar mapping co-located with existing agent config patterns.

Alternatives considered:
- Extending `RealtimeAgent` objects with custom fields: rejected due to SDK type constraints and coupling risk.

### 5. Baseline alignment with explicit deviation note

Decision:
- Preserve baseline architecture boundaries (UI-only change, same hooks/routes/tooling).
- Accept one intentional UX deviation: user mode hides debug controls while maintaining always-available mode switch.

Rationale:
- Meets product requirement without altering runtime architecture.
- Makes deviation auditable and reversible.

## Risks / Trade-offs

- [Risk] Users in user mode may not immediately find connect/debug controls.
  → Mitigation: keep Debug toggle always visible and clearly labeled; ensure immediate switch to debug mode reveals full controls.

- [Risk] Persisted `debugMode` may retain unexpected state between sessions.
  → Mitigation: default to `false` when key is absent/invalid; keep toggle as immediate override.

- [Risk] Missing avatar assets or unmapped agents can produce broken visuals.
  → Mitigation: always resolve through fallback image (`defaultBaseImage`) and render placeholder-safe panel.

- [Risk] Future phases (audio-reactive overlays) could blur scope boundaries.
  → Mitigation: enforce phase gate in specs/tasks: no sound-level hook or overlay switching in this change.

## Migration Plan

1. Add mode state and persistence in `App.tsx`.
2. Add mode-gated right panel rendering (`Avatar` vs `Events`).
3. Add `BottomToolbar` mode props and always-visible debug toggle.
4. Add `avatarConfig.ts` and `Avatar.tsx` static rendering path.
5. Add at least one scenario avatar mapping for end-to-end validation.
6. Verify manual behavior: both modes accessible, persistence works, no regressions in session and transcript flows.

Rollback:
- Revert mode-gated rendering to baseline always-`Events` panel.
- Remove `debugMode` preference reads/writes.
- Restore always-visible footer controls.

## Open Questions

- Should user mode eventually expose a minimal connect affordance without entering debug mode?
- Should agent switches in disconnected state update avatar immediately or only after session attach?
