## Context

The project started as an Azure-first deployment with Streamlit frontend. It has since migrated to portable Docker Compose with FastAPI + React. Documentation was partially updated but `app-use-case.md` still has a large historical section (lines 113-307) with Azure-specific setup instructions that reference scripts, tables, and workflows that no longer exist.

## Goals / Non-Goals

**Goals:**
- Remove Azure-as-requirement language from all active docs
- Preserve historical content in `docs/archive/` for reference
- Present Azure as an optional deployment target
- Make docs reflect the current Docker-first setup

**Non-Goals:**
- Rewriting the entire documentation (just cleanup Azure refs)
- Creating new Azure deployment guides
- Changing `.env.example` files (already neutral)

## Decisions

### 1. Move historical section, don't delete
The Streamlit/Azure section in `app-use-case.md` has historical value. Move to `docs/archive/legacy-azure-streamlit-setup.md` rather than deleting.

### 2. Replace "Azure OpenAI" with "OpenAI / Azure OpenAI" in architecture docs
The adapter supports both providers via `OPENAI_PROVIDER` env var. Docs should reflect this.

## File change list

| File | Status | Description |
|------|--------|-------------|
| `docs/app-use-case.md` | (modified) | Remove historical section, update Azure refs to neutral |
| `docs/architecture.md` | (modified) | Replace "Azure OpenAI" with "OpenAI / Azure OpenAI" |
| `docs/semantic-search.md` | (modified) | Update if Azure-specific refs exist |
| `docs/archive/legacy-azure-streamlit-setup.md` | (new) | Moved historical content |
| `CHANGELOG.md` | (modified) | Update Unreleased |

## Rollback strategy

Restore moved content from `docs/archive/` back to `app-use-case.md`. No code changes to revert.
