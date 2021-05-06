import os
import random
import sys

import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or, CommandNotFound, has_permissions, NoPrivateMessage

from db import db
from voting import voteDB

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.reactions = True
intents.members = True


def get_prefix(bot, message: discord.Message):
    prefix = voteDB.getPrefix(message.guild.id if message.guild else -1)
    return when_mentioned_or(prefix)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')
    await resume_posting()


async def resume_posting():
    # TODO
    pass


# Prefix set command
@has_permissions(administrator=True)
@bot.command(name='prefix', help='Changes prefix on the server')
async def prefix(ctx, prefix: str):
    voteDB.setPrefix(ctx.guild.id, prefix)
    await ctx.send(f"Prefix changed to `{prefix}`")


@bot.event
async def on_error(ctx, err, *args, **kwargs):
    if err == "on_command_error":
        await args[0].send("Something went wrong")
    raise


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        pass
    elif isinstance(error, NoPrivateMessage):
        await ctx.send("Cannot run this command in DMs")
    elif hasattr(error, "original"):
        raise error.original
    else: raise error


# Load poll functionality
bot.load_extension("voting.polls")

bot.run(TOKEN)
