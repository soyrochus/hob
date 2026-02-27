## ADDED Requirements

### Requirement: Avatar SHALL render sound-reactive overlay levels
The `Avatar` component SHALL derive a discrete sound level from realtime AI audio output and SHALL render overlays by level as follows: `0` = no overlay, `1` = `overlay-1`, `2` = `overlay-2`, `3` = `overlay-3`, `4` = `overlay-4`.

#### Scenario: Overlay frame changes during speech
- **WHEN** AI audio amplitude rises into a non-zero level
- **THEN** `Avatar` renders the overlay image mapped to the current level

#### Scenario: Overlay is hidden during silence
- **WHEN** AI audio amplitude is below the silence threshold and level resolves to `0`
- **THEN** `Avatar` renders no overlay layer

### Requirement: App SHALL provide AI audio element to avatar
`App.tsx` SHALL pass the SDK audio element used for AI playback to `Avatar` so overlay level analysis is driven by actual model output audio.

#### Scenario: Avatar receives SDK audio element
- **WHEN** user mode renders `Avatar`
- **THEN** `Avatar` receives `audioElement={sdkAudioElement}` from `App.tsx`

## MODIFIED Requirements

### Requirement: Avatar configuration SHALL be resolved by selected agent
The application SHALL resolve avatar display configuration from an agent-keyed map using `selectedAgentName`, and SHALL pass the resolved configuration to `Avatar`, including base image and optional overlay image overrides.

#### Scenario: Agent switch updates avatar source
- **WHEN** the selected agent changes to an agent with a configured base image
- **THEN** `Avatar` updates to use that agent's configured base image

### Requirement: Avatar SHALL provide fallback behavior for missing configuration
If no avatar configuration exists for the selected agent, the application SHALL use a default base image and SHALL still render a valid avatar panel without runtime errors. If overlay image paths are not configured for the selected agent, the application SHALL use default overlay image paths.

#### Scenario: Missing config uses default image
- **WHEN** the selected agent has no matching entry in the avatar config map
- **THEN** `Avatar` renders using the default base image

#### Scenario: Missing overlay config uses default overlays
- **WHEN** the selected agent lacks overlay image overrides
- **THEN** `Avatar` resolves overlay image paths from global defaults

## REMOVED Requirements

### Requirement: Initial avatar implementation SHALL remain static
**Reason**: Phase 2 introduces required sound-reactive overlays tied to realtime AI audio output.
**Migration**: Replace static-only avatar rendering with level-based overlay rendering in `Avatar` and `useAvatarAudioLevel`.
