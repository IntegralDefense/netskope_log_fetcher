"""Module to hold helper classes shared across tests."""


class AsyncHelper:
    """ Class wrapper for helper functions. When unit testing async
    style stuffz, an 'await' statement expects a coroutine; Therefore,
    we wrap the desired outcome with a coroutine. It's kind of like
    a mock for coroutines.
    """

    @staticmethod
    async def value(val):
        """ Coroutine wrapper for mocking with return values."""

        return val

    @staticmethod
    async def error(error, *args, **kwargs):
        """ Coroutine wrapper for mocking forced exceptions/errors."""

        raise error(*args, **kwargs)
