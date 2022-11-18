#!/usr/bin/env python3
import asyncio
import logging
from typing import Literal, Optional

import discord
from discord import Intents
from discord.ext import commands
from discord.ext.commands import Bot, Context, Greedy, check, when_mentioned_or
from discord_simple_pretty_help import SimplePrettyHelp

from config import CONFIG
from utils.utils import done_react, is_compsoc_exec_in_guild, wait_react

DESCRIPTION = """
Votebot Time 😎
"""

# The command extensions to be loaded by the bot
EXTENSIONS = [
    "cogs.commands.vote",
    "cogs.commands.roomsearch",
]


intents = Intents.default()
intents.members = True
intents.message_content = True

bot = Bot(
    command_prefix=when_mentioned_or(CONFIG.PREFIX),
    description=DESCRIPTION,
    intents=intents,
    help_command=SimplePrettyHelp(),
)


@bot.command()
@check(is_compsoc_exec_in_guild)
@done_react
async def reload_cogs(ctx: Context):
    for extension in EXTENSIONS:
        await bot.reload_extension(extension)


@bot.event
async def on_ready():
    logging.info("Logged in as")
    logging.info(str(bot.user))
    logging.info("------")


async def main():
    logging.basicConfig(level=logging.WARNING)

    async with bot:
        for extension in EXTENSIONS:
            try:
                logging.info(f"Attempting to load extension {extension}")
                await bot.load_extension(extension)
            except Exception as e:
                logging.exception("Failed to load extension {extension}", exc_info=e)
        await bot.start(CONFIG.DISCORD_TOKEN)


@bot.command()
@commands.guild_only()
@check(is_compsoc_exec_in_guild)
@done_react
@wait_react
async def sync(ctx: Context) -> None:
    """
    Syncs slash commands to server
    """
    synced = await ctx.bot.tree.sync()
    await ctx.send(f"Synced {len(synced)} commands globally to the current guild.")


if __name__ == "__main__":
    asyncio.run(main())
