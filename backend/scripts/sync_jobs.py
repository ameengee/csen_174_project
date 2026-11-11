import asyncio
from datetime import UTC, datetime

import httpx2
import structlog

from backend.clients import close_clients, db_transaction, get_pool
from backend.configs.constants import JOB_SOURCE_TIMEOUT
from backend.database.job_postings import delete_unseen, upsert_postings
from backend.database.schema import apply_schema
from backend.services.job_sources import (
    INTERNSHIPS_URL,
    NEW_GRAD_URL,
    Posting,
    fetch_greenhouse,
    fetch_simplify,
    greenhouse_level,
    greenhouse_posting,
    greenhouse_slugs,
    simplify_posting,
)

log = structlog.get_logger(__name__)


async def _save(source: str, postings: list[Posting], started: datetime) -> None:
    """Replace one source's postings with a fresh download, in one transaction."""
    unique = list({p.id: p for p in postings}.values())
    async with db_transaction() as conn:
        await upsert_postings(conn, unique)
        removed = await delete_unseen(conn, source, started)
    log.info("job_source_saved", source=source, postings=len(unique), removed=removed)


async def sync_job_postings() -> None:
    """Download all sources and save them. A source that fails to download is left as is."""
    started = datetime.now(UTC)
    await apply_schema(await get_pool())

    async with httpx2.AsyncClient(timeout=JOB_SOURCE_TIMEOUT) as client:
        internships = await fetch_simplify(client, INTERNSHIPS_URL)
        new_grad = await fetch_simplify(client, NEW_GRAD_URL)
        await _save(
            "SimplifyJobs",
            [simplify_posting(r, "internship") for r in internships]
            + [simplify_posting(r, "entry_level") for r in new_grad],
            started,
        )

        greenhouse = await fetch_greenhouse(client, greenhouse_slugs(internships + new_grad))
        postings = []
        for job in greenhouse:
            level = greenhouse_level(job["title"])
            if level is not None:
                postings.append(greenhouse_posting(job, level))
        await _save("Greenhouse", postings, started)


async def _main() -> None:
    try:
        await sync_job_postings()
    finally:
        await close_clients()


if __name__ == "__main__":
    asyncio.run(_main())
