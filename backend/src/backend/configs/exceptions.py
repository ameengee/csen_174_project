class InvalidRequestError(Exception):
    """The caller sent something we can reject before doing any work (-> 400)."""


class UnauthorizedError(Exception):
    """The caller is not authenticated (-> 401)."""


class UpstreamError(Exception):
    """An external service (e.g. the OpenAI API) failed or gave an unusable answer (-> 502)."""


class NotFoundError(Exception):
    """The requested resource does not exist, or does not belong to this caller (-> 404)."""
