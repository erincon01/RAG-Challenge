## MODIFIED Requirements

### Requirement: Token budget enforcement in RAG pipeline

Before calling the LLM for answer generation, the system SHALL count the total input tokens
(system message + context + question) using `tiktoken`.

When total input tokens exceed `max_input_tokens` from the `SearchRequest`:
- The system SHALL iteratively remove the lowest-ranked search result from the context
- The system SHALL continue removing results until the total fits within the budget
- The system SHALL log the number of results truncated

The system MUST NOT call the LLM if zero search results remain after truncation.
In that case, it SHALL return an error indicating the question is too long for the budget.

### Requirement: Token usage metadata

The response metadata SHALL include:
- `input_tokens`: actual token count sent to the LLM
- `max_input_tokens`: the budget limit from the request
- `results_truncated`: number of search results dropped to fit the budget (0 if none)

#### Scenario: Context fits within budget
- **GIVEN** a search returning 5 results with combined context of 3,000 tokens
- **AND** `max_input_tokens` is 10,000
- **WHEN** the answer is generated
- **THEN** all 5 results SHALL be included in the context
- **AND** `results_truncated` SHALL be 0

#### Scenario: Context exceeds budget and is truncated
- **GIVEN** a search returning 10 results with combined context of 15,000 tokens
- **AND** `max_input_tokens` is 10,000
- **WHEN** the answer is generated
- **THEN** the system SHALL drop lowest-ranked results until tokens fit
- **AND** `results_truncated` SHALL reflect the number dropped

#### Scenario: Question alone exceeds budget
- **GIVEN** a question whose tokens alone exceed `max_input_tokens`
- **WHEN** the answer is generated
- **THEN** the system SHALL return an error without calling the LLM
