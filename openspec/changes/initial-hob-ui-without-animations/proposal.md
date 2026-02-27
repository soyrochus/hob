## Why

The current UI mixes user-facing and developer-facing controls, and always shows the logs panel as the right-side content. We need a clear user mode with a persona/avatar panel while preserving a dedicated debug mode, and we need this now to establish the base Hob UI before adding sound-reactive visuals.

## What Changes

- Add a persistent `isDebugMode` toggle in `App.tsx` (stored in `localStorage` as `debugMode`) with default `false`.
- In the main content area, render `Avatar` in user mode and `Events` in debug mode.
- Update `BottomToolbar` to keep only the Debug toggle always visible; make existing debug controls (Connect, PTT, Audio, Logs, Codec) invisible in user mode while preserving bar height.
- Add a new `Avatar` component for the right panel in user mode, with static base image rendering only (no sound-level overlays or animation in this change).
- Add avatar configuration support via a new `avatarConfig` map keyed by agent name, with default base image and overlay path defaults for future phases.
- Wire `App.tsx` to resolve `selectedAgentName` into avatar config and pass it to `Avatar`.
- Populate at least one scenario with an avatar config entry to validate end-to-end config flow.

## Capabilities

### New Capabilities

- `debug-mode-ui-toggle`: Provide a persistent UI mode switch that controls right-panel content and footer control visibility, while keeping the Debug toggle always accessible.
- `agent-avatar-panel`: Provide a user-mode avatar panel with agent-specific base-image configuration and fallback behavior, without sound-reactive overlay behavior.

### Modified Capabilities

- None.

## Impact

- Affected code: `src/app/App.tsx`, `src/app/components/BottomToolbar.tsx`, new `src/app/components/Avatar.tsx`, new `src/app/agentConfigs/avatarConfig.ts`, and at least one scenario agent config file.
- APIs/contracts: `BottomToolbar` prop contract expands with `isDebugMode` and `setIsDebugMode`; `Avatar` receives agent config from app state.
- Dependencies/systems: browser `localStorage` usage expands to include `debugMode`; no new external runtime dependencies expected.
