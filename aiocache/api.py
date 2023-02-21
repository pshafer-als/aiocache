import asyncio
import functools
import logging
import os
import time
from typing import Callable, Set


logger = logging.getLogger(__name__)


class API:

    CMDS: Set[Callable[..., object]] = set()

    @classmethod
    def register(cls, func):
        API.CMDS.add(func)
        return func

    @classmethod
    def unregister(cls, func):
        API.CMDS.discard(func)

    @classmethod
    def timeout(cls, func):
        """
        This decorator sets a maximum timeout for a coroutine to execute. The timeout can be both
        set in the ``self.timeout`` attribute or in the ``timeout`` kwarg of the function call.
        I.e if you have a function ``get(self, key)``, if its decorated with this decorator, you
        will be able to call it with ``await get(self, "my_key", timeout=4)``.

        Use 0 or None to disable the timeout.
        """
        NOT_SET = "NOT_SET"

        @functools.wraps(func)
        async def _timeout(self, *args, timeout=NOT_SET, **kwargs):
            timeout = self.timeout if timeout == NOT_SET else timeout
            if timeout == 0 or timeout is None:
                return await func(self, *args, **kwargs)
            return await asyncio.wait_for(func(self, *args, **kwargs), timeout)

        return _timeout

    @classmethod
    def aiocache_enabled(cls, fake_return=None):
        """
        Use this decorator to be able to fake the return of the function by setting the
        ``AIOCACHE_DISABLE`` environment variable
        """

        def enabled(func):
            @functools.wraps(func)
            async def _enabled(*args, **kwargs):
                if os.getenv("AIOCACHE_DISABLE") == "1":
                    return fake_return
                return await func(*args, **kwargs)

            return _enabled

        return enabled

    @classmethod
    def plugins(cls, func):
        @functools.wraps(func)
        async def _plugins(self, *args, **kwargs):
            start = time.monotonic()
            for plugin in self.plugins:
                await getattr(plugin, "pre_{}".format(func.__name__))(self, *args, **kwargs)

            ret = await func(self, *args, **kwargs)

            end = time.monotonic()
            for plugin in self.plugins:
                await getattr(plugin, "post_{}".format(func.__name__))(
                    self, *args, took=end - start, ret=ret, **kwargs
                )
            return ret

        return _plugins
