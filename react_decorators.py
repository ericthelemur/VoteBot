import functools
from discord.ext.commands import Context


def wait_react(func):
    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        ctx: Context = next(a for a in args if isinstance(a, Context))
        await ctx.message.add_reaction("🕐")
        await func(*args, **kwargs)
        await ctx.message.remove_reaction("🕐", ctx.me)
    return decorator


def done_react(func):
    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        ctx: Context = next(a for a in args if isinstance(a, Context))
        await func(*args, **kwargs)
        await ctx.message.add_reaction("👍")
    return decorator


def remove_command(func):
    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        ctx: Context = next(a for a in args if isinstance(a, Context))
        await func(*args, **kwargs)
        await ctx.message.delete()
    return decorator