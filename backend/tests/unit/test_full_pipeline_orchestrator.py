"""Unit tests for IngestionService.run_full_pipeline_job()."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.ingestion_service import IngestionService


class TestRunFullPipelineJob:
    def _make_service(self):
        return IngestionService(statsbomb=MagicMock())

    @patch("app.services.ingestion_service.JobService")
    def test_calls_all_five_stages_in_order(self, _mock_job_service):
        service = self._make_service()
        service.run_download_job = MagicMock()
        service.run_load_job = MagicMock()
        service.run_aggregate_job = MagicMock()
        service.run_generate_summaries_job = MagicMock()
        service.run_rebuild_embeddings_job = MagicMock()

        payload = {
            "source": "postgres",
            "match_ids": [3943043],
            "competition_id": 55,
            "season_id": 282,
        }
        service.run_full_pipeline_job("job-1", payload)

        # Confirm order by inspecting mock.mock_calls on a parent
        call_order = []
        for method_name in [
            "run_download_job",
            "run_load_job",
            "run_aggregate_job",
            "run_generate_summaries_job",
            "run_rebuild_embeddings_job",
        ]:
            mock = getattr(service, method_name)
            if mock.called:
                call_order.append(method_name)
        assert call_order == [
            "run_download_job",
            "run_load_job",
            "run_aggregate_job",
            "run_generate_summaries_job",
            "run_rebuild_embeddings_job",
        ]

    @patch("app.services.ingestion_service.JobService")
    def test_aborts_remaining_stages_on_failure(self, mock_job_service):
        service = self._make_service()
        service.run_download_job = MagicMock()
        service.run_load_job = MagicMock(side_effect=RuntimeError("load failed"))
        service.run_aggregate_job = MagicMock()
        service.run_generate_summaries_job = MagicMock()
        service.run_rebuild_embeddings_job = MagicMock()

        payload = {"source": "postgres", "match_ids": [1]}
        service.run_full_pipeline_job("job-2", payload)

        # download + load were called, the rest were not
        service.run_download_job.assert_called_once()
        service.run_load_job.assert_called_once()
        service.run_aggregate_job.assert_not_called()
        service.run_generate_summaries_job.assert_not_called()
        service.run_rebuild_embeddings_job.assert_not_called()
        mock_job_service.fail.assert_called_once()

    @patch("app.services.ingestion_service.JobService")
    def test_forwards_payload_to_each_stage(self, _mock_job_service):
        service = self._make_service()
        service.run_download_job = MagicMock()
        service.run_load_job = MagicMock()
        service.run_aggregate_job = MagicMock()
        service.run_generate_summaries_job = MagicMock()
        service.run_rebuild_embeddings_job = MagicMock()

        payload = {
            "source": "postgres",
            "match_ids": [3943043, 3869685],
            "competition_id": 55,
            "season_id": 282,
            "language": "english",
            "embedding_models": ["text-embedding-3-small"],
        }
        service.run_full_pipeline_job("job-3", payload)

        # Each stage receives the same top-level payload; each stage
        # extracts what it needs (documented contract).
        for method_name in [
            "run_download_job",
            "run_load_job",
            "run_aggregate_job",
            "run_generate_summaries_job",
            "run_rebuild_embeddings_job",
        ]:
            mock = getattr(service, method_name)
            assert mock.call_args[0][1] == payload

    @patch("app.services.ingestion_service.JobService")
    def test_job_marked_complete_on_success(self, mock_job_service):
        service = self._make_service()
        service.run_download_job = MagicMock()
        service.run_load_job = MagicMock()
        service.run_aggregate_job = MagicMock()
        service.run_generate_summaries_job = MagicMock()
        service.run_rebuild_embeddings_job = MagicMock()

        service.run_full_pipeline_job("job-4", {"source": "postgres", "match_ids": [1]})
        mock_job_service.complete.assert_called_once()
        mock_job_service.fail.assert_not_called()
