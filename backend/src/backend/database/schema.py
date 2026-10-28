import asyncpg

# Idempotent; applied on startup. Add new tables here until we need real migrations.
SCHEMA = """
CREATE TABLE IF NOT EXISTS job_postings (
    id TEXT PRIMARY KEY,          -- "<source>:<id in that source>"
    source TEXT NOT NULL,
    level TEXT NOT NULL,          -- internship | entry_level | mid_level | senior
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL,
    url TEXT NOT NULL,
    posted DATE,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS job_postings_level_posted ON job_postings (level, posted DESC);
"""


async def apply_schema(pool: asyncpg.Pool) -> None:
    """Create any missing tables and indexes."""
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)
