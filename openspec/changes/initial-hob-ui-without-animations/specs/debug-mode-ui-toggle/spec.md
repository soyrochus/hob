## ADDED Requirements

### Requirement: Application SHALL support exactly two UI modes
The application SHALL support exactly two UI modes, `user` and `debug`, controlled by a single boolean source of truth in `App.tsx` (`isDebugMode`). The default mode on first load SHALL be `user` (`isDebugMode = false`).

#### Scenario: Initial load defaults to user mode
- **WHEN** no previously stored mode preference exists
- **THEN** the UI starts in user mode with `isDebugMode` set to `false`

### Requirement: UI mode preference SHALL persist across sessions
The application SHALL persist the current debug mode preference in browser local storage using the key `debugMode`, and SHALL restore that preference on subsequent loads.

#### Scenario: Previously enabled debug mode is restored
- **WHEN** local storage contains `debugMode=true` before application load
- **THEN** the application restores debug mode and renders debug-mode UI on startup

### Requirement: Debug toggle SHALL always be available
The bottom toolbar SHALL include a Debug toggle that remains visible and interactive in both user mode and debug mode, allowing the user to switch modes at any time.

#### Scenario: Mode can be switched from user mode
- **WHEN** the application is currently in user mode and the user enables the Debug toggle
- **THEN** the application transitions immediately to debug mode

### Requirement: Right panel content SHALL be mode-dependent
In user mode, the right panel SHALL render `Avatar`. In debug mode, the right panel SHALL render `Events`.

#### Scenario: Right panel switches with mode
- **WHEN** the user toggles from user mode to debug mode
- **THEN** the right panel content changes from `Avatar` to `Events`

### Requirement: Debug controls SHALL be hidden in user mode and shown in debug mode
The existing debug controls (`Connect`, `PTT`, `Audio`, `Logs`, `Codec`) SHALL be visible in debug mode and SHALL be visually hidden in user mode while preserving the toolbar layout footprint.

#### Scenario: Footer controls are hidden in user mode
- **WHEN** the application is in user mode
- **THEN** debug controls are not visually shown while the toolbar height remains stable
