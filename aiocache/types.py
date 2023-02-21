"""
This module declares types that are used in multiple modules throughout this package.
"""

class BasePlugin:
    @classmethod
    def add_hook(cls, func, hooks):
        for hook in hooks:
            setattr(cls, hook, func)

    async def do_nothing(self, *args, **kwargs):
        pass
