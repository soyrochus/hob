## 1. App Mode State And Routing

- [ ] 1.1 Add `isDebugMode` state in `src/app/App.tsx` with default `false` and restore from `localStorage` key `debugMode`.
- [ ] 1.2 Persist `isDebugMode` changes back to `localStorage` and ensure invalid/missing stored values fall back to user mode.
- [ ] 1.3 Implement explicit right-panel routing in `App.tsx` so user mode renders `Avatar` and debug mode renders `Events`.
- [ ] 1.4 Pass `isDebugMode` and `setIsDebugMode` to `BottomToolbar` from `App.tsx`.

## 2. Bottom Toolbar Mode Behavior

- [ ] 2.1 Extend `src/app/components/BottomToolbar.tsx` props with `isDebugMode` and `setIsDebugMode`.
- [ ] 2.2 Keep Debug toggle always visible and interactive in both modes.
- [ ] 2.3 Render existing debug controls (`Connect`, `PTT`, `Audio`, `Logs`, `Codec`) as visually hidden in user mode and visible in debug mode using layout-preserving styling.
- [ ] 2.4 Verify mode switch from user mode to debug mode is immediate and does not require reload.

## 3. Avatar Configuration And Component

- [ ] 3.1 Create `src/app/agentConfigs/avatarConfig.ts` with `AvatarConfig`, `avatarConfigs`, `defaultBaseImage`, and default overlay path constants for future phases.
- [ ] 3.2 Create `src/app/components/Avatar.tsx` for static base-image rendering only (no audio-reactive logic, overlays, or animation).
- [ ] 3.3 Wire `App.tsx` to resolve avatar config from `selectedAgentName` and pass resolved config to `Avatar`.
- [ ] 3.4 Add at least one scenario avatar mapping entry and verify agent switching updates the rendered base image.
- [ ] 3.5 Implement fallback behavior so missing agent config uses `defaultBaseImage` without runtime errors.

## 4. Validation And Baseline Checks

- [ ] 4.1 Manually validate both required modes exist and are reachable at all times through the always-visible Debug toggle.
- [ ] 4.2 Validate startup persistence scenarios: no stored value => user mode; stored `true` => debug mode; stored `false` => user mode.
- [ ] 4.3 Confirm user mode shows `Avatar` and hides debug controls while preserving bottom toolbar height.
- [ ] 4.4 Confirm debug mode shows `Events` and full debug controls.
- [ ] 4.5 Confirm no Phase 2 behavior is introduced (no sound-level hook usage, no overlay swapping, no animations).
