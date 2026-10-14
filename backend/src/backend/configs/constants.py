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

# -----------------------------
# Profile intake
# -----------------------------
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # LinkedIn PDFs are small; data-export zips can be a few MB
MAX_ZIP_MEMBER_BYTES = 2 * 1024 * 1024  # per CSV we keep, guards against zip bombs
PROFILE_ANALYSIS_MAX_TOKENS = 16000
