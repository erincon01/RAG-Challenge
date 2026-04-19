## ADDED Requirements

### Requirement: Tutorials directory with step-by-step guides
The project SHALL include a `docs/tutorials/` directory with at least 3 self-contained tutorials that a developer can follow from start to finish using the seed data and local Docker stack.

#### Scenario: Tutorials use live curl commands against local stack
- **GIVEN** a developer has the Docker stack running with seed data
- **WHEN** they follow a tutorial's curl commands
- **THEN** all commands SHALL return valid responses from the local PostgreSQL (pgvector) backend

### Requirement: Golden set for evaluation
The project SHALL include a `data/golden_set.json` file with 10+ questions, each with match_id, expected answer keywords, and search parameters.

#### Scenario: Golden set questions return relevant answers
- **GIVEN** seed data is loaded
- **WHEN** each golden set question is submitted to the chat search API
- **THEN** the response SHALL contain at least one of the expected answer keywords
