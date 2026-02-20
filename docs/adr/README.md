# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the RAG Challenge project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:

- **Title**: Short noun phrase
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: What is the issue that we're seeing that is motivating this decision?
- **Decision**: What is the change that we're actually proposing or doing?
- **Consequences**: What becomes easier or more difficult to do because of this change?

## Index

| ADR | Title | Status | Date | Implementation |
|-----|-------|--------|------|----------------|
| [001](ADR-001-layered-architecture.md) | Adoption of Layered Architecture | ✅ Accepted | 2026-02-08 | ✅ Implemented |
| [002](ADR-002-centralized-configuration.md) | Centralized Configuration with Pydantic Settings | ✅ Accepted | 2026-02-08 | ✅ Implemented |
| [003](ADR-003-pgvector-migration.md) | Migration from Azure AI Extensions to pgvector | ✅ Accepted | 2026-02-20 | ✅ Implemented |
| [004](ADR-004-local-docker-infrastructure.md) | Local Docker Infrastructure with SQL Server 2025 Express and PostgreSQL | ✅ Accepted | 2026-02-08 | ✅ Implemented |

## Naming Convention

ADRs are numbered sequentially and should use the following naming format:

```
ADR-XXX-short-title.md
```

Where:
- `XXX` is a three-digit number (001, 002, etc.)
- `short-title` is a kebab-case title

## When to Write an ADR

Write an ADR when:
- Making a significant architectural decision
- Choosing between multiple viable alternatives
- Making a decision that will be hard to reverse
- Making a decision that affects multiple teams or components
- Documenting a decision that will impact future development

## References

- [Michael Nygard's ADR template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub organization](https://adr.github.io/)
