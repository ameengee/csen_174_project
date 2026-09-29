class InvalidRequestError(Exception):
    """The caller sent something we can reject before doing any work (-> 400)."""


class UnauthorizedError(Exception):
    """The caller is not authenticated (-> 401)."""


class NotFoundError(Exception):
    """The requested resource does not exist, or does not belong to this caller (-> 404)."""
