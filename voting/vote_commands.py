import discord
from discord.ext import commands
from discord.ext.commands import Bot

from voting import voteDB
from react_decorators import *
from voting.symbols import symbols
from voting.parsers import *


# Main poll class, mainly a wrapper around Vote
from voting.vote_manager import VoteManager


class Voting(commands.Cog):
    bot: Bot

    def __init__(self, bot):
        self.bot = bot
        self.vm = VoteManager(bot)


    @commands.command(name="createpoll", aliases=["poll", "secretpoll"], help=poll_parser.format_help())
    @commands.guild_only()
    @wait_react
    async def create_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):  # Extra checks past the parser's basic ones. These are caught and forwarded in run_parser
                if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                if args.winners <= 0: raise argparse.ArgumentError(win_arg, f"Cannot select less than 1 winner.")
                if args.limit <= 0: raise argparse.ArgumentError(lim_arg, f"Cannot have limit less than 1.")
                for op in args.options:
                    if len(op) > 50: raise argparse.ArgumentError(opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

            args = run_parser(poll_parser, options, extra_checks)
            # Send feedback or run vote
            if isinstance(args, str): await ctx.send(args)
            else:
                await self.vm.std_vote(ctx, args)

        # Catch any exception, to ensure the bot continues running for other votes
        # and to give error message due to error messages in async blocks not being reported otherwise
        except Exception as e:
            print(e)
            raise e


    @commands.command(name="visiblepoll", aliases=["vpoll"], help=("Runs a poll with visible votes.\n" + vis_poll_parser.format_help()))
    @commands.guild_only()
    @wait_react
    async def create_visible_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):  # Extra checks past the parser's basic ones. These are caught and forwarded in run_parser
                if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                if args.winners <= 0: raise argparse.ArgumentError(win_arg, f"Cannot select less than 1 winner.")
                if args.limit <= 0: raise argparse.ArgumentError(lim_arg, f"Cannot have limit less than 1.")
                for op in args.options:
                    if len(op) > 50: raise argparse.ArgumentError(opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

            args = run_parser(vis_poll_parser, options, extra_checks)
            # Send feedback or run vote
            if isinstance(args, str):
                await ctx.send(args)
            else:
                await self.vm.visible_poll(ctx, args)

        # Catch any exception, to ensure the bot continues running for other votes
        # and to give error message due to error messages in async blocks not being reported otherwise
        except Exception as e:
            print(e)
            raise e



    @commands.command(name="stvpoll", help=("Runs a STV poll.\n" + stv_parser.format_help()))
    @commands.guild_only()
    @wait_react
    async def create_stv_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):
                if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                if args.winners <= 0: raise argparse.ArgumentError(win_arg, f"Cannot select less than 1 winner.")
                if args.limit <= 0: raise argparse.ArgumentError(lim_arg, f"Cannot have limit less than 1.")
                for op in args.options:
                    if len(op) > 50: raise argparse.ArgumentError(stv_opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

            args = run_parser(stv_parser, options, extra_checks)
            if isinstance(args, str): await ctx.send(args)
            else:
                await self.vm.stv_vote(ctx, args)

        except Exception as e:
            print(e)
            raise e


    @commands.command(name="close", aliases=["closepoll", "closevote"], help="Ends a poll with ID `pid`")
    @done_react
    @wait_react
    async def close_poll(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            await self.vm.close(vid)
        else: await ctx.send("You cannot end this poll")


    @commands.command(name="voters", help="Gets the number of people who have voted in a poll.")
    @wait_react
    async def voters(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            voters = voteDB.getVoterCount(vid)
            await ctx.send(f"{voters} people have voted so far in vote {vid}.")


    @commands.command(name="myvotes", help="Will DM with your current votes for vote `vid`.")
    @wait_react
    @done_react
    async def myvotes(self, ctx: Context, vid: int):
        user = ctx.author
        await user.create_dm()

        options = [x[1] for x in voteDB.getOptions(vid)]
        uvs = voteDB.getUserVotes(vid, user.id)

        if not uvs: await user.dm_channel.send(f"Poll {vid}: You have no votes so far.")
        else: await user.dm_channel.send(
                f"Poll {vid}: Your current votes are:\n\t\t" +
                '\n\t\t'.join(f"{symbols[i]} **{options[i]}**" for i, _ in uvs)
            )



    @commands.command(name="halt", help="Ends a vote early with no results page.")
    @wait_react
    @done_react
    async def halt(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            await self.vm.halt(vid)


    @commands.Cog.listener()
    @commands.guild_only()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        user = self.bot.get_user(reaction.user_id)
        emoji = str(reaction.emoji)

        guild: discord.Guild = self.bot.get_guild(reaction.guild_id)
        if not guild: return  # In DM, ignore
        channel: discord.TextChannel = guild.get_channel(reaction.channel_id)
        message: discord.Message = await channel.fetch_message(reaction.message_id)

        if user.bot: return
        await self.vm.on_reaction_add(reaction, emoji, message, user)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_raw_reaction_remove(self, reaction: discord.RawReactionActionEvent):
        user = self.bot.get_user(reaction.user_id)
        emoji = str(reaction.emoji)

        guild: discord.Guild = self.bot.get_guild(reaction.guild_id)
        if not guild: return  # In DM, ignore
        channel: discord.TextChannel = guild.get_channel(reaction.channel_id)
        message: discord.Message = await channel.fetch_message(reaction.message_id)

        if user.bot: return
        await self.vm.on_reaction_remove(reaction, emoji, message, user)


# Register module with bot
def setup(bot):
    bot.add_cog(Voting(bot))

