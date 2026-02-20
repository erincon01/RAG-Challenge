#!/bin/bash
set -eu

echo "============================================"
echo "[post-start] Starting services..."
echo "============================================"

echo "[post-start] Starting uvicorn in background..."
cd /app && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app > /tmp/uvicorn.log 2>&1 &

echo "[post-start] Running health checks..."
python - <<'PY'
import socket
import time

import requests


def check(name, url, validator, max_attempts=30, sleep_s=2):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.get(url, timeout=5)
            if validator(r):
                print(f"  {name}: OK")
                return True
            last_error = f"status={r.status_code} body={r.text[:200]}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(sleep_s)
    print(f"  {name}: FAILED ({last_error})")
    return False


def is_host_reachable(host, port):
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        return True
    except (OSError, socket.timeout):
        return False


ok = check("backend-liveness", "http://localhost:8000/api/v1/health/live",
           lambda r: r.status_code == 200)
if not ok:
    raise SystemExit("[post-start] Backend failed to start. Check /tmp/uvicorn.log")

check("backend-readiness", "http://localhost:8000/api/v1/health/ready",
      lambda r: r.status_code == 200)

if is_host_reachable("frontend", 5173):
    check("frontend", "http://frontend:5173/", lambda r: r.status_code == 200, max_attempts=10)
else:
    print("  frontend: not running (skipped)")

print("[post-start] Health checks completed.")
PY
