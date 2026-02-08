#!/usr/bin/env bash
set -euo pipefail

echo "[post-start] Running service health checks..."
python - <<'PY'
import time
import requests

checks = [
    ("backend-liveness", "http://localhost:8000/api/v1/health/live", lambda r: r.status_code == 200),
    ("backend-readiness", "http://localhost:8000/api/v1/health/ready", lambda r: r.status_code == 200 and r.json().get("ready") is True),
    ("frontend-health", "http://frontend:8501/_stcore/health", lambda r: r.status_code == 200),
    ("postgres-smoke", "http://localhost:8000/api/v1/competitions?source=postgres", lambda r: r.status_code == 200),
]

for name, url, validator in checks:
    last_error = None
    for attempt in range(1, 31):
        try:
            response = requests.get(url, timeout=5)
            if validator(response):
                print(f"[post-start] {name}: OK")
                break
            last_error = f"unexpected response: {response.status_code} {response.text[:200]}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(2)
    else:
        raise SystemExit(f"[post-start] {name} failed after retries: {last_error}")

print("[post-start] All checks passed.")
PY
