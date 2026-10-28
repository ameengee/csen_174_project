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
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # LinkedIn profile PDFs are well under this
PROFILE_ANALYSIS_MAX_TOKENS = 16000

# -----------------------------
# Job search
# -----------------------------
JOB_SOURCE_TIMEOUT = 30.0  # seconds per download
MAX_COMPANY_BOARDS = 120  # Greenhouse boards fetched for mid/senior roles
MAX_SEARCH_CANDIDATES = 1200  # jobs sent to the model after keyword filtering
CLASSIFY_BATCH_SIZE = 100  # jobs per model call; smaller batches finish faster in parallel
CLASSIFY_CONCURRENCY = 12
MAX_JOBS_PER_ROLE = 100
