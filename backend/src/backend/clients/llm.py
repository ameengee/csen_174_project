from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def get_openai() -> AsyncOpenAI:
    """Get or create the AsyncOpenAI client singleton (reads OPENAI_API_KEY)."""
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


async def close_openai() -> None:
    """Close the AsyncOpenAI client and its HTTP connections."""
    global _client
    if _client is None:
        return
    await _client.close()
    _client = None
