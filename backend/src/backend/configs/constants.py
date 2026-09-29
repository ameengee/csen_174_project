# -----------------------------
# Service
# -----------------------------
API_VERSION = "0.1.0"
SERVICE_NAME = "csen174-backend"

# -----------------------------
# Health
# -----------------------------
RESTART_THRESHOLD = 5  # background worker restarts before /healthz reports degraded
EXTERNAL_SERVICE_TIMEOUT = 3.0  # seconds a readiness check may wait on a dependency

# -----------------------------
# Retries
# -----------------------------
POOL_RETRIES = 3
DB_RETRIES = 3
