# RAG-Challenge — developer convenience targets
#
# Run from the repo root. Most targets expect the docker-compose stack to
# be up (see README.md / docs/getting-started.md). Inside the devcontainer
# you can also run `cd backend && python -m scripts.<name>` directly.

.PHONY: help seed seed-force seed-postgres seed-sqlserver test lint format

help:
	@echo "Available targets:"
	@echo "  seed             Load pre-computed seed dataset (Euro 2024 + WC 2022 finals) into both DBs"
	@echo "  seed-force       Re-load seed even if already present"
	@echo "  seed-postgres    Load seed into Postgres only"
	@echo "  seed-sqlserver   Load seed into SQL Server only"
	@echo "  test             Run backend pytest suite"
	@echo "  lint             Ruff lint check on backend/app"
	@echo "  format           Ruff format on backend/app"

seed:
	cd backend && python -m scripts.seed_load --source both

seed-force:
	cd backend && python -m scripts.seed_load --source both --force

seed-postgres:
	cd backend && python -m scripts.seed_load --source postgres

seed-sqlserver:
	cd backend && python -m scripts.seed_load --source sqlserver

test:
	cd backend && pytest tests/ -v

lint:
	ruff check backend/app

format:
	ruff format backend/app
