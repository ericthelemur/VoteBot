import os
import random

import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or, CommandNotFound, has_permissions

from db import db
from voting import voteDB

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.reactions = True
intents.members = True


def get_prefix(bot, message: discord.Message):
    prefix = voteDB.getPrefix(message.guild.id)
    return when_mentioned_or(prefix)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')
    await reload_messages()

async def reload_messages():
    # Load previous messages into cache (so on_reaction_add picks up on them)
    messages = voteDB.getMessages()

    for vid, gid, cid, mid in messages:
        guild: discord.Guild = bot.get_guild(gid)
        channel: discord.TextChannel = guild.get_channel(cid)
        message: discord.Message = await channel.fetch_message(mid)
        print("Loading message ", message.id)


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
    elif hasattr(error, "original"):
        raise error.original
    else: raise error


# Load poll functionality
bot.load_extension("voting.polls")

bot.run(TOKEN)
