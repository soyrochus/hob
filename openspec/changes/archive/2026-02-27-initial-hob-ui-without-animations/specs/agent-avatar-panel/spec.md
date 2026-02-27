## ADDED Requirements

### Requirement: User mode SHALL render an avatar panel
When the application is in user mode, the right panel SHALL render an `Avatar` component instead of the `Events` panel.

#### Scenario: Avatar panel shown in user mode
- **WHEN** `isDebugMode` is `false`
- **THEN** the right panel renders `Avatar`

### Requirement: Avatar configuration SHALL be resolved by selected agent
The application SHALL resolve avatar display configuration from an agent-keyed map using `selectedAgentName`, and SHALL pass the resolved configuration to `Avatar`.

#### Scenario: Agent switch updates avatar source
- **WHEN** the selected agent changes to an agent with a configured base image
- **THEN** `Avatar` updates to use that agent's configured base image

### Requirement: Avatar SHALL provide fallback behavior for missing configuration
If no avatar configuration exists for the selected agent, the application SHALL use a default base image and SHALL still render a valid avatar panel without runtime errors.

#### Scenario: Missing config uses default image
- **WHEN** the selected agent has no matching entry in the avatar config map
- **THEN** `Avatar` renders using the default base image

### Requirement: Initial avatar implementation SHALL remain static
This change SHALL implement only static avatar rendering and SHALL NOT include sound-level analysis, overlay frame switching, or animation behavior.

#### Scenario: No audio-reactive behavior in phase 1
- **WHEN** the application is running this change's implementation
- **THEN** avatar rendering remains static and independent of realtime audio amplitude
