## Why

The avatar panel is currently static, which misses a key voice-first affordance: visual feedback that tracks active AI speech. We need a sound-reactive overlay now to make user mode feel responsive and expressive while preserving the already-implemented user/debug mode foundation.

## What Changes

- Add realtime audio-level detection for the AI output stream using a new `useAvatarAudioLevel` hook based on Web Audio API analysis of `sdkAudioElement`.
- Update `Avatar` to accept `audioElement`, compute a discrete sound level (`0..4`), and render overlay frames on top of the base avatar image.
- Use overlay frame selection rules: level `0` shows no overlay; levels `1..4` map to `overlay-1` through `overlay-4`.
- Add overlay assets under `public/avatars/overlays/` and wire `Avatar` to use default overlay paths (with optional per-agent overrides from avatar config).
- Update `App.tsx` to pass `audioElement={sdkAudioElement}` to `Avatar` in user mode.
- Tune and validate RMS threshold mapping so overlay changes are visible during speech and silent at rest.
- Preserve all existing mode behavior: debug mode still renders `Events`, and user mode still renders `Avatar`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `agent-avatar-panel`: Extend avatar behavior from static rendering to audio-reactive overlay rendering driven by realtime AI audio output.

## Impact

- Affected code: `src/app/components/Avatar.tsx`, `src/app/App.tsx`, new `src/app/hooks/useAvatarAudioLevel.ts`, and `src/app/agentConfigs/avatarConfig.ts` (overlay path usage/overrides).
- Affected assets: new overlay files in `public/avatars/overlays/overlay-{1,2,3,4}.png`.
- APIs/contracts: `Avatar` props expand to include `audioElement`; avatar configuration may use overlay path settings.
- Dependencies/systems: introduces in-browser `AudioContext`/`AnalyserNode` processing for visual state only; no backend/API contract changes.
