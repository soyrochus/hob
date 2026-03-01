## ADDED Requirements

### Requirement: Default assistant scenario is available
The system SHALL define a new `defaultAssistant` scenario with a single realtime `assistant` agent and make it selectable through the same scenario registry path used by existing scenarios.

#### Scenario: Scenario is registered in agent sets
- **WHEN** the application loads agent configuration sets
- **THEN** `defaultAssistant` MUST be present in `allAgentSets` and resolve to a valid realtime agent array

#### Scenario: Scenario is available in SDK scenario map
- **WHEN** `connectToRealtime` resolves the scenario key from `agentConfig`
- **THEN** `defaultAssistant` MUST map to a valid scenario in `sdkScenarioMap`

### Requirement: Assistant delegates hosted-tool work via supervisor responses
The system SHALL delegate tasks requiring hosted tools to the supervisor text pathway through `/api/responses` using the existing supervisor delegation pattern.

#### Scenario: Hosted-tool request is delegated
- **WHEN** the realtime assistant determines the user intent requires hosted tools
- **THEN** the assistant MUST invoke supervisor delegation and send a Responses API request through `/api/responses`

#### Scenario: Delegation uses hosted tools payload
- **WHEN** the supervisor request is constructed for delegated work
- **THEN** the request MUST include hosted tool declarations for `web_search` and `code_interpreter`

### Requirement: File search support is optional and safe
The system SHALL support optional `file_search` usage in the default assistant flow without breaking behavior when document search is not configured.

#### Scenario: File search enabled
- **WHEN** document search is configured for the deployment
- **THEN** supervisor delegation MUST be able to include `file_search` in the hosted tools set

#### Scenario: File search not configured
- **WHEN** document search configuration is absent
- **THEN** the assistant MUST continue operating without runtime failure and without requiring `file_search`

### Requirement: Existing scenarios remain backward compatible
The system SHALL preserve behavior of existing demo scenarios while adding `defaultAssistant`.

#### Scenario: Existing scenario routing unaffected
- **WHEN** a user selects an existing scenario key already supported before this change
- **THEN** the app MUST continue to resolve and connect that scenario without requiring any `defaultAssistant` logic

#### Scenario: Existing responses proxy contract unchanged
- **WHEN** any scenario calls `/api/responses`
- **THEN** the request/response contract MUST remain compatible with current supervisor helper usage

### Requirement: Default scenario choice is configuration-level
The system SHALL allow `defaultAssistant` to be set as the default scenario through configuration (`defaultAgentSetKey`) without requiring UI changes.

#### Scenario: Default set points to default assistant
- **WHEN** `defaultAgentSetKey` is configured as `defaultAssistant`
- **THEN** first-load scenario selection MUST use `defaultAssistant`

#### Scenario: Default set remains existing value
- **WHEN** `defaultAgentSetKey` is not changed
- **THEN** current default startup behavior MUST remain unchanged
