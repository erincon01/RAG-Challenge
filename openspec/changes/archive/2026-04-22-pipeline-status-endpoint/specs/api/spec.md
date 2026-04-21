## ADDED Requirements

### Requirement: Pipeline status per match
The system SHALL expose `GET /api/v1/ingestion/pipeline-status?source=X` returning per-match pipeline state.

#### Scenario: Returns status for all matches in source
- **GIVEN** matches are loaded in the database
- **WHEN** `GET /api/v1/ingestion/pipeline-status?source=postgres` is called
- **THEN** response SHALL contain an array of objects with: match_id, display_name, events_count, agg_count, summary_count, embedding_count
