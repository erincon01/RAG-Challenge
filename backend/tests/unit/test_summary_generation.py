"""Unit tests for the summary-generation stage of IngestionService."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.adapters.openai_client import OpenAIAdapter
from app.services.ingestion_service import IngestionService


# ---------------------------------------------------------------------------
# Prompt template loading
# ---------------------------------------------------------------------------


class TestLoadPromptTemplate:
    def test_template_file_exists_and_is_non_empty(self):
        template_path = (
            Path(__file__).resolve().parents[2]
            / "app"
            / "services"
            / "prompts"
            / "event_summary.md"
        )
        assert template_path.exists(), f"Missing template at {template_path}"
        content = template_path.read_text(encoding="utf-8")
        assert len(content) > 100
        # Sanity: must contain all expected placeholders
        for placeholder in (
            "{language}",
            "{competition_name}",
            "{match_date}",
            "{home_team}",
            "{away_team}",
            "{period}",
            "{minute}",
            "{quarter_minute}",
            "{events_json}",
        ):
            assert placeholder in content, (
                f"Placeholder {placeholder} missing from template"
            )

    def test_template_formats_without_keyerror(self):
        service = IngestionService(statsbomb=MagicMock())
        template = service._load_prompt_template()
        formatted = template.format(
            language="english",
            competition_name="UEFA Euro",
            match_date="2024-07-14",
            home_team="Spain",
            away_team="England",
            period=1,
            minute=10,
            quarter_minute=2,
            events_json='{"type": "Pass"}',
        )
        assert "Spain" in formatted
        assert "England" in formatted
        assert "{" not in formatted.replace("{", "__OPEN__").replace(
            "__OPEN__", ""
        )  # no remaining placeholders

    def test_template_is_cached_after_first_load(self):
        service = IngestionService(statsbomb=MagicMock())
        first = service._load_prompt_template()
        second = service._load_prompt_template()
        assert first is second  # identity, not equality — confirms cache


# ---------------------------------------------------------------------------
# _fetch_aggregation_rows_for_summary
# ---------------------------------------------------------------------------


class TestFetchAggregationRowsForSummary:
    def test_postgres_filters_null_summary_and_match_ids(self):
        service = IngestionService(statsbomb=MagicMock())
        cur = MagicMock()
        cur.fetchall.return_value = [
            (1, 1, 10, 2, '{"type": "Pass"}'),
            (2, 1, 10, 3, '{"type": "Shot"}'),
        ]
        conn = MagicMock()
        conn.cursor.return_value = cur

        rows = service._fetch_aggregation_rows_for_summary(conn, "postgres", [3943043])

        assert len(rows) == 2
        assert rows[0] == (1, 1, 10, 2, '{"type": "Pass"}')
        # Confirm SQL uses the right table + filters
        sql = cur.execute.call_args[0][0]
        assert "events_details__quarter_minute" in sql
        assert "summary IS NULL" in sql
        assert "match_id = ANY" in sql

    def test_sqlserver_uses_correct_table(self):
        service = IngestionService(statsbomb=MagicMock())
        cur = MagicMock()
        cur.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = cur

        service._fetch_aggregation_rows_for_summary(
            conn, "sqlserver", [3943043, 3869685]
        )

        sql = cur.execute.call_args[0][0]
        assert "events_details__15secs_agg" in sql
        assert "summary IS NULL" in sql
        # SQL Server uses ? placeholders, one per match_id
        assert sql.count("?") == 2

    def test_empty_match_ids_selects_all_null_summary_rows(self):
        service = IngestionService(statsbomb=MagicMock())
        cur = MagicMock()
        cur.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = cur

        service._fetch_aggregation_rows_for_summary(conn, "postgres", [])

        sql = cur.execute.call_args[0][0]
        assert "summary IS NULL" in sql
        assert "match_id" not in sql.split("WHERE")[1]


# ---------------------------------------------------------------------------
# _update_summary_for_row
# ---------------------------------------------------------------------------


class TestUpdateSummaryForRow:
    def test_postgres_uses_percent_s_placeholder(self):
        service = IngestionService(statsbomb=MagicMock())
        cur = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value = cur

        service._update_summary_for_row(conn, "postgres", 42, "Spain attacks.")

        sql, params = cur.execute.call_args[0]
        assert "events_details__quarter_minute" in sql
        assert "%s" in sql
        assert "?" not in sql
        assert params == ("Spain attacks.", 42)

    def test_sqlserver_uses_question_mark_placeholder(self):
        service = IngestionService(statsbomb=MagicMock())
        cur = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value = cur

        service._update_summary_for_row(conn, "sqlserver", 7, "Goal!")

        sql, params = cur.execute.call_args[0]
        assert "events_details__15secs_agg" in sql
        assert "?" in sql
        assert "%s" not in sql
        assert params == ("Goal!", 7)


# ---------------------------------------------------------------------------
# _fetch_match_info_for_prompt
# ---------------------------------------------------------------------------


class TestFetchMatchInfoForPrompt:
    def test_returns_dict_keyed_by_match_id(self):
        service = IngestionService(statsbomb=MagicMock())
        cur = MagicMock()
        cur.fetchall.return_value = [
            (
                3943043,
                "UEFA Euro",
                "2024-07-14",
                "Spain",
                "England",
            ),
        ]
        conn = MagicMock()
        conn.cursor.return_value = cur

        info = service._fetch_match_info_for_prompt(conn, "postgres", [3943043])

        assert 3943043 in info
        assert info[3943043]["competition_name"] == "UEFA Euro"
        assert info[3943043]["home_team"] == "Spain"
        assert info[3943043]["away_team"] == "England"

    def test_missing_match_returns_placeholder_info(self):
        service = IngestionService(statsbomb=MagicMock())
        cur = MagicMock()
        cur.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = cur

        info = service._fetch_match_info_for_prompt(conn, "postgres", [123])

        # No crash, just empty dict
        assert info == {}


# ---------------------------------------------------------------------------
# run_generate_summaries_job
# ---------------------------------------------------------------------------


class TestRunGenerateSummariesJob:
    def _make_service(self):
        service = IngestionService(statsbomb=MagicMock())
        return service

    @patch("app.services.ingestion_service.OpenAIAdapter")
    @patch("app.services.ingestion_service.JobService")
    def test_happy_path_calls_chat_and_updates_row(
        self, mock_job_service, mock_adapter_cls
    ):
        service = self._make_service()
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.create_chat_completion.return_value = "Spain attacks."
        mock_adapter_cls.return_value = mock_adapter

        # Mock connection with match info + aggregation rows
        cur = MagicMock()
        # First fetchall: match info for prompt
        # Second fetchall: aggregation rows
        cur.fetchall.side_effect = [
            [(3943043, "UEFA Euro", "2024-07-14", "Spain", "England")],
            [(1, 1, 10, 2, '{"type":"Pass"}'), (2, 1, 10, 3, '{"type":"Shot"}')],
        ]
        conn = MagicMock()
        conn.cursor.return_value = cur

        with patch.object(service, "_get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = conn
            mock_get_conn.return_value.__exit__.return_value = False

            service.run_generate_summaries_job(
                "job-1", {"source": "postgres", "match_ids": [3943043]}
            )

        # Chat completion called once per row
        assert mock_adapter.create_chat_completion.call_count == 2
        # Job completed
        mock_job_service.complete.assert_called_once()
        mock_job_service.fail.assert_not_called()

    @patch("app.services.ingestion_service.OpenAIAdapter")
    @patch("app.services.ingestion_service.JobService")
    def test_skips_rows_with_empty_events_json(
        self, mock_job_service, mock_adapter_cls
    ):
        service = self._make_service()
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.create_chat_completion.return_value = "Narration."
        mock_adapter_cls.return_value = mock_adapter

        cur = MagicMock()
        cur.fetchall.side_effect = [
            [(3943043, "UEFA Euro", "2024-07-14", "Spain", "England")],
            [
                (1, 1, 10, 2, ""),  # empty events → skip
                (2, 1, 10, 3, '{"type":"Shot"}'),  # valid → process
            ],
        ]
        conn = MagicMock()
        conn.cursor.return_value = cur

        with patch.object(service, "_get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = conn
            mock_get_conn.return_value.__exit__.return_value = False

            service.run_generate_summaries_job(
                "job-2", {"source": "postgres", "match_ids": [3943043]}
            )

        # Only called for non-empty row
        assert mock_adapter.create_chat_completion.call_count == 1

    @patch("app.services.ingestion_service.OpenAIAdapter")
    @patch("app.services.ingestion_service.JobService")
    def test_continues_on_partial_row_failure(self, mock_job_service, mock_adapter_cls):
        service = self._make_service()
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        # First call raises, second succeeds
        mock_adapter.create_chat_completion.side_effect = [
            RuntimeError("boom"),
            "Second narration.",
        ]
        mock_adapter_cls.return_value = mock_adapter

        cur = MagicMock()
        cur.fetchall.side_effect = [
            [(3943043, "UEFA Euro", "2024-07-14", "Spain", "England")],
            [
                (1, 1, 10, 2, '{"type":"Pass"}'),
                (2, 1, 10, 3, '{"type":"Shot"}'),
            ],
        ]
        conn = MagicMock()
        conn.cursor.return_value = cur

        with patch.object(service, "_get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = conn
            mock_get_conn.return_value.__exit__.return_value = False

            service.run_generate_summaries_job(
                "job-3", {"source": "postgres", "match_ids": [3943043]}
            )

        # Both rows attempted
        assert mock_adapter.create_chat_completion.call_count == 2
        # Job still completes (doesn't fail on single-row error)
        mock_job_service.complete.assert_called_once()

    @patch("app.services.ingestion_service.OpenAIAdapter")
    @patch("app.services.ingestion_service.JobService")
    def test_strips_summary_whitespace(self, mock_job_service, mock_adapter_cls):
        service = self._make_service()
        mock_adapter = MagicMock(spec=OpenAIAdapter)
        mock_adapter.create_chat_completion.return_value = (
            "  \n  Spain attacks.  \n\n  "
        )
        mock_adapter_cls.return_value = mock_adapter

        cur = MagicMock()
        cur.fetchall.side_effect = [
            [(3943043, "UEFA Euro", "2024-07-14", "Spain", "England")],
            [(1, 1, 10, 2, '{"type":"Pass"}')],
        ]
        conn = MagicMock()
        conn.cursor.return_value = cur

        with patch.object(service, "_get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = conn
            mock_get_conn.return_value.__exit__.return_value = False

            service.run_generate_summaries_job(
                "job-4", {"source": "postgres", "match_ids": [3943043]}
            )

        # Find the UPDATE call
        update_calls = [
            c for c in cur.execute.call_args_list if "UPDATE" in str(c.args[0]).upper()
        ]
        assert len(update_calls) == 1
        params = update_calls[0].args[1]
        assert params[0] == "Spain attacks."  # stripped
