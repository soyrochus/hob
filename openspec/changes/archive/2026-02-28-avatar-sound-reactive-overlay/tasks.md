## 1. Overlay Assets And Config Wiring

- [x] 1.1 Add overlay assets at `public/avatars/overlays/overlay-1.png` through `overlay-4.png` (or temporary placeholders until final designer files land).
- [x] 1.2 Ensure `src/app/agentConfigs/avatarConfig.ts` exposes default overlay paths and supports optional per-agent overlay overrides.
- [x] 1.3 Validate asset path conventions match runtime usage (`/avatars/overlays/...`) and work in Next.js static serving.

## 2. Audio-Level Hook

- [x] 2.1 Create `src/app/hooks/useAvatarAudioLevel.ts` with signature accepting `HTMLAudioElement | null | undefined` and returning `0 | 1 | 2 | 3 | 4`.
- [x] 2.2 Implement Web Audio graph setup (`MediaElementSource -> AnalyserNode`) with safe one-time source initialization guards.
- [x] 2.3 Implement RMS calculation and threshold mapping to levels (`0..4`) per design thresholds.
- [x] 2.4 Add cleanup for animation frame loop and audio resources to prevent leaks across unmount/reconnect cycles.
- [x] 2.5 Add lightweight update throttling and/or level-change-only state updates to avoid unnecessary re-renders.

## 3. Avatar And App Integration

- [x] 3.1 Update `src/app/components/Avatar.tsx` to accept `audioElement` prop and call `useAvatarAudioLevel(audioElement)`.
- [x] 3.2 Implement overlay layering in `Avatar`: base image always visible, overlay rendered only when level `> 0`, and level-to-file mapping (`overlay-1..4`).
- [x] 3.3 Resolve overlay image paths from per-agent config when present, otherwise from default overlay paths.
- [x] 3.4 Update `src/app/App.tsx` to pass `audioElement={sdkAudioElement}` to `Avatar` in user mode.
- [x] 3.5 Confirm existing mode contract remains unchanged: user mode shows `Avatar`; debug mode shows `Events`.

## 4. Behavior Validation

- [x] 4.1 Verify in user mode that overlay changes visibly while AI audio is playing.
- [x] 4.2 Verify silence behavior: level `0` results in no overlay.
- [x] 4.3 Verify missing agent overlay overrides still render via default overlays.
- [x] 4.4 Verify no regressions in debug mode panel behavior or toolbar mode switching.
- [x] 4.5 Verify Phase 2 scope boundaries: no extra animation system beyond overlay frame selection; no backend/API changes.
