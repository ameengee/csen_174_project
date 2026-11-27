from typing import Any

from backend.clients import db_transaction


async def get_user(email: str) -> dict[str, Any] | None:
    """The user with this email, or None."""
    async with db_transaction(readonly=True) as conn:
        row = await conn.fetchrow(
            "SELECT email, password_hash, full_name, verified FROM users WHERE email = $1",
            email.lower(),
        )
    return dict(row) if row else None


async def create_user(
    email: str, password_hash: str, full_name: str | None, verified: bool
) -> bool:
    """Insert a user. False if the email is already registered."""
    async with db_transaction() as conn:
        status: str = await conn.execute(
            """
            INSERT INTO users (email, password_hash, full_name, verified)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (email) DO NOTHING
            """,
            email.lower(),
            password_hash,
            full_name,
            verified,
        )
    return status.endswith(" 1")


async def mark_verified(email: str) -> bool:
    """Mark a user's email verified. False if there is no such user."""
    async with db_transaction() as conn:
        status: str = await conn.execute(
            "UPDATE users SET verified = true WHERE email = $1", email.lower()
        )
    return status.endswith(" 1")


async def set_password(email: str, password_hash: str) -> bool:
    """Replace a user's password hash. False if there is no such user."""
    async with db_transaction() as conn:
        status: str = await conn.execute(
            "UPDATE users SET password_hash = $2 WHERE email = $1", email.lower(), password_hash
        )
    return status.endswith(" 1")
