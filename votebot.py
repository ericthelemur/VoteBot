import os
import random
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')


# Basic test command
@bot.command(name='roll', help='Simulates rolling dice.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [random.choice(range(1, number_of_sides + 1)) for _ in range(number_of_dice)]
    await ctx.send(', '.join(map(str, dice)) + f": %d" % sum(dice))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

# Load poll functionality
bot.load_extension("polls")

bot.run(TOKEN)
