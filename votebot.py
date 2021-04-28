import os
import random
from discord.ext import commands
from discord.ext.commands import when_mentioned_or, CommandNotFound

from db import db

TOKEN = os.getenv('DISCORD_TOKEN')


def get_prefix(bot, message):
    return when_mentioned_or("+")(bot, message)
bot = commands.Bot(command_prefix=get_prefix)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')


# Basic test command
@bot.command(name='roll', help='Simulates rolling dice.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [random.choice(range(1, number_of_sides + 1)) for _ in range(number_of_dice)]
    await ctx.send(', '.join(map(str, dice)) + f": %d" % sum(dice))


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

    # if isinstance(error, commands.errors.CheckFailure):
    #     await ctx.send('You do not have the correct role for this command.')


# Load poll functionality
bot.load_extension("voting.polls")

bot.run(TOKEN)
