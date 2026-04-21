## MODIFIED Requirements

### Requirement: Operations page shows pipeline as numbered steps
The Operations page SHALL display the ingestion pipeline as 5 clearly numbered and titled step cards in order: Download, Load, Aggregate, Summaries, Embeddings.

#### Scenario: All 5 steps visible
- **GIVEN** user navigates to `/operations`
- **WHEN** the page loads
- **THEN** 5 pipeline step cards SHALL be visible with titles: Download, Load, Aggregate, Summaries, Embeddings

#### Scenario: Each step has an action button
- **GIVEN** user views the Operations page
- **WHEN** they look at any pipeline step card
- **THEN** the card SHALL contain an action button to execute that step
