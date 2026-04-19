## 1. Archive legacy content

- [x] 1.1 Move historical section (lines 113-307) from `docs/app-use-case.md` to `docs/archive/legacy-azure-streamlit-setup.md`
- [x] 1.2 Add a note at the top of the archived file: "Historical reference — see docs/app-use-case.md for current architecture"

## 2. Update app-use-case.md

- [x] 2.1 Remove the historical section (now in archive)
- [x] 2.2 Replace "Azure OpenAI" with "OpenAI" or "OpenAI / Azure OpenAI" in the current section
- [x] 2.3 Replace "Azure SQL" / "Azure SQL Server" with "SQL Server" in the current section
- [x] 2.4 Add a note: "Azure is supported as an optional deployment target — see OPENAI_PROVIDER env var"

## 3. Update architecture.md

- [x] 3.1 Replace "Azure OpenAI" with "OpenAI / Azure OpenAI" throughout
- [x] 3.2 Replace "Azure SQL Server" with "SQL Server" throughout

## 4. Update semantic-search.md

- [x] 4.1 Check for Azure-specific references and update to neutral language

## 5. Final validation

- [x] 5.1 Grep for remaining "Azure" refs in active docs (excluding archive/, adr/, conversation_log)
- [x] 5.2 Update CHANGELOG.md under `## [Unreleased]`
