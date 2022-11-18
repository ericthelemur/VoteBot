import functools
import re
import textwrap
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Union

import dateparser
import discord
from discord.ext.commands import CommandError, Context
from more_itertools import partition

from config import CONFIG
from models import db_session


class AdminError(CommandError):
    message = None

    def __init__(self, message=None, *args):
        self.message = message
        super().__init__(*args)


class EnumGet:
    """Only use this if you're an enum inheriting it!"""

    @classmethod
    def get(cls, argument: str, default=None):
        values = {e.name.casefold(): e.name for e in list(cls)}
        casefolded = argument.casefold()
        if casefolded not in values:
            return default
        else:
            return cls[values[casefolded]]


def clean_brackets(
    string,
    brackets=(("(", ")"),),
):
    """Removes matching brackets from the outside of a string
    Only supports single-character brackets
    """
    while len(string) > 1 and (string[0], string[-1]) in brackets:
        string = string[1:-1]
    return string


def filter_out_none(iterable: Iterable, /):
    return (i for i in iterable if i is not None)


def format_list(el: list, /):
    if len(el) == 1:
        return f"{el[0]}"
    elif len(el) == 2:
        return f"{el[0]} and {el[1]}"
    else:
        return f'{", ".join(el[:-1])}, and {el[-1]}'


def format_list_of_members(members, /, *, ping=True):
    if ping:
        el = [member.mention for member in members]
    else:
        el = [str(member) for member in members]
    return format_list(el)


async def is_compsoc_exec_in_guild(ctx: Context, /):
    """Check whether a member is an exec in the UWCS Discord"""
    compsoc_guild = next(
        (guild for guild in ctx.bot.guilds if guild.id == CONFIG.UWCS_DISCORD_ID), None
    )
    if not compsoc_guild:
        return False
    compsoc_member = compsoc_guild.get_member(ctx.message.author.id)
    if not compsoc_member:
        return False

    roles = [
        discord.utils.get(compsoc_member.roles, id=x) for x in CONFIG.ADMIN_ROLE_IDS
    ]
    return any(roles)


def is_decimal(num):
    try:
        Decimal(num)
        return True
    except (InvalidOperation, TypeError):
        return False


def parse_time(time, /):
    # dateparser.parse returns None if it cannot parse
    parsed_time = dateparser.parse(
        time, settings={"DATE_ORDER": "DMY", "PREFER_DATES_FROM": "future"}
    )

    now = datetime.now()

    if not parsed_time:
        try:
            parsed_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
        except ValueError:
            pass

    if not parsed_time:
        try:
            parsed_time = datetime.strptime(time, "%m-%d %H:%M")
            parsed_time = parsed_time.replace(year=now.year)
            if parsed_time < now:
                parsed_time = parsed_time.replace(year=now.year + 1)
        except ValueError:
            pass

    if not parsed_time:
        try:
            parsed_time = datetime.strptime(time, "%H:%M:%S")
            parsed_time = parsed_time.replace(
                year=now.year, month=now.month, day=now.day
            )
            if parsed_time < now:
                parsed_time = parsed_time + timedelta(days=1)

        except ValueError:
            pass

    if not parsed_time:
        try:
            parsed_time = datetime.strptime(time, "%H:%M")
            parsed_time = parsed_time.replace(
                year=now.year, month=now.month, day=now.day
            )
            if parsed_time < now:
                parsed_time = parsed_time + timedelta(days=1)
        except ValueError:
            pass

    if not parsed_time:
        result = re.match(r"(\d+d)?\s*(\d+h)?\s*(\d+m)?\s*(\d+s)?(?!^)$", time)
        if result:
            parsed_time = now
            if result.group(1):
                parsed_time = parsed_time + timedelta(days=int(result.group(1)[:-1]))
            if result.group(2):
                parsed_time = parsed_time + timedelta(hours=int(result.group(2)[:-1]))
            if result.group(3):
                parsed_time = parsed_time + timedelta(minutes=int(result.group(3)[:-1]))
            if result.group(4):
                parsed_time = parsed_time + timedelta(seconds=int(result.group(4)[:-1]))

    return parsed_time


def partition_list(pred, el, /):
    a, b = partition(pred, el)
    return list(a), list(b)


def pluralise(el, /, word, single="", plural="s"):
    if len(el) > 1:
        return word + plural
    else:
        return word + single


def user_is_irc_bot(ctx):
    return ctx.author.id == CONFIG.UWCS_DISCORD_BRIDGE_BOT_ID


def replace_external_emoji(guild, string):
    """References to external emojis aren't updated by default. Can be used so bot only emojis don't pollute server pool"""
    from votebot import bot

    def emotes(match: re.Match):
        # If emoji body
        if match.group(2):
            # Prioritize local emoji
            e: discord.Emoji = discord.utils.get(guild.emojis, name=match.group(2))
            if e is None:  # If no local, check all servers the bot is in
                e = discord.utils.get(bot.emojis, name=match.group(2))
            if e is not None:
                return match.group(1) + str(e)
        return match.group(0)

    return re.sub("(^|[^<]):([-_a-zA-Z0-9]+):", emotes, string)


def split_into_messages(sections: Union[str, List[str]], limit=4096):
    """Split a string (or list of sections) into small enough chunks to send (4096 chars)"""
    if isinstance(sections, str):
        sections = [sections]

    sections = "§".join(sections)
    result = split_by(
        [
            lambda x: x.split("§"),
            lambda x: x.split("\n"),  # Then split by lines
            lambda x: textwrap.wrap(
                x, width=limit
            ),  # Then split within lines, using textwrap
        ],
        sections,
        limit,
    )
    result = [x.replace("§", "\n") for x in result]
    return result


def split_by(split_funcs, section, limit=4000):
    """Split section by each of split_funcs in descending order until each chunk is smaller than limit"""
    section = section.replace("\n\n", "\n_ _\n")
    if len(section) <= limit:
        return [section.strip("\n")]  # Base case
    else:
        parts = split_funcs[0](section)
        accum = ""
        result = []
        for part in parts:
            # For each part (as split by first of split_funcs), attempt to accumulate
            new_accum = accum + "\n" + part
            # If short enough, combine with previous parts in accumulator
            if len(new_accum) <= limit:
                accum = new_accum
            else:  # If too long, clear accumulator, and attempt next level of split
                if accum:
                    result.append(accum.strip("\n"))
                result += split_by(split_funcs[1:], part, limit)
                accum = ""
        # Add any tail to result
        if accum:
            result.append(accum.strip("\n"))
        return result


def wait_react(func):
    """
    Reacts to the command message with a clock while message processing is ongoing
    Most useful on commands with longer processing times
    """

    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        ctx: Context = next(a for a in args if isinstance(a, Context))
        await ctx.message.add_reaction("🕐")
        await func(*args, **kwargs)
        if ctx:
            await ctx.message.remove_reaction("🕐", ctx.me)

    return decorator


def done_react(func):
    """
    Reacts to the command message with a thumbs up once command processing is complete
    Most useful on commands with no direct result message
    """

    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        ctx: Context = next(a for a in args if isinstance(a, Context))
        await func(*args, **kwargs)
        if ctx:
            await ctx.message.add_reaction("👍")

    return decorator


def rerun_to_confirm(key_name, confirm_msg="Re-run to confirm"):
    """
    Records the first run of the command, only actuall runs command on confirmatory second run
    """
    first_run_times = {}

    def decorator_actual(func):
        @functools.wraps(func)
        async def decorator(*args, **kwargs):
            ctx: Context = next(a for a in args if isinstance(a, Context))
            if kwargs[key_name] not in first_run_times:
                first_run_times[kwargs[key_name]] = datetime.now()
                return await ctx.send(confirm_msg, ephemeral=True)

            timeout_threshold = datetime.now() - timedelta(minutes=5)
            if timeout_threshold > first_run_times[kwargs[key_name]]:
                # If previous run is more than 5 mins ago (timeout after 5)
                first_run_times[kwargs[key_name]] = datetime.now()
                return await ctx.send(confirm_msg, ephemeral=True)

            await func(*args, **kwargs)

        return decorator

    return decorator_actual
