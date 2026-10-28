from datetime import datetime

import asyncpg

from backend.clients import db_transaction
from backend.services.job_sources import Job, Level, Posting


async def upsert_postings(conn: asyncpg.Connection, postings: list[Posting]) -> None:
    """Insert new postings and refresh existing ones (marking them as seen now)."""
    await conn.executemany(
        """
        INSERT INTO job_postings (id, source, level, company, title, location, url, posted)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (id) DO UPDATE SET
            level = EXCLUDED.level,
            company = EXCLUDED.company,
            title = EXCLUDED.title,
            location = EXCLUDED.location,
            url = EXCLUDED.url,
            posted = EXCLUDED.posted,
            last_seen_at = now()
        """,
        [
            (p.id, p.source, p.level, p.company, p.title, p.location, p.url, p.posted)
            for p in postings
        ],
    )


async def delete_unseen(conn: asyncpg.Connection, source: str, since: datetime) -> int:
    """Delete postings from a source that the latest sync no longer saw (they've closed)."""
    status: str = await conn.execute(
        "DELETE FROM job_postings WHERE source = $1 AND last_seen_at < $2", source, since
    )
    return int(status.split()[-1])


async def list_postings(level: Level) -> list[Job]:
    """All stored postings at a level, newest first."""
    async with db_transaction(readonly=True) as conn:
        rows = await conn.fetch(
            """
            SELECT company, title, location, url, posted, source
            FROM job_postings
            WHERE level = $1
            ORDER BY posted DESC NULLS LAST
            """,
            level,
        )
    return [Job(**dict(r)) for r in rows]
