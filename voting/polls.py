import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot

from voting import voteDB
from voting.symbols import symbols
from voting.parsers import *


# Main poll class, mainly a wrapper around Vote
from voting.vote_manager import VoteManager


class Polls(commands.Cog):
    bot: Bot

    def __init__(self, bot):
        self.bot = bot
        self.vm = VoteManager(bot)


    @commands.command(name="createpoll", aliases=["poll", "secretpoll"], help=poll_parser.format_help())
    @commands.guild_only()
    async def create_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):  # Extra checks past the parser's basic ones. These are caught and forwarded in run_parser
                if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                if args.winners <= 0: raise argparse.ArgumentError(stv_win_arg, f"STV cannot select less than 1 winner.")
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


    @commands.command(name="quickpoll", aliases=["qpoll"], help=("Runs a quick poll.\n" + vis_poll_parser.format_help()))
    @commands.guild_only()
    async def create_quick_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):  # Extra checks past the parser's basic ones. These are caught and forwarded in run_parser
                if len(args.options) == 1 or len(args.options) > 20: raise argparse.ArgumentError(vis_opt_arg, f"Either none or between 2 and 20 options must be supplied.")
                for op in args.options:
                    if len(op) > 50: raise argparse.ArgumentError(vis_opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

            args = run_parser(vis_poll_parser, options, extra_checks)
            # Send feedback or run vote
            if isinstance(args, str):
                await ctx.send(args)
            else:
                await self.vm.quick_poll(ctx, args)

        # Catch any exception, to ensure the bot continues running for other votes
        # and to give error message due to error messages in async blocks not being reported otherwise
        except Exception as e:
            print(e)
            raise e



    @commands.command(name="stvpoll", help=("Runs a STV poll.\n" + stv_parser.format_help()))
    @commands.guild_only()
    async def create_stv_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):
                if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(stv_opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                if args.winners <= 0: raise argparse.ArgumentError(stv_win_arg, f"STV cannot select less than 1 winner.")

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
    async def close_poll(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            await self.vm.close(vid)
        else: await ctx.send("You cannot end this poll")


    @commands.command(name="voters", help="Gets the number of people who have voted in a poll.")
    async def voters(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            voters = voteDB.getVoterCount(vid)
            await ctx.send(f"{voters} people have voted so far in vote {vid}.")


    @commands.command(name="halt", help="Ends a vote early with no results page.")
    async def halt(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            await self.vm.halt(vid)


    @commands.Cog.listener()
    @commands.guild_only()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        user = self.bot.get_user(reaction.user_id)
        emoji = str(reaction.emoji)

        guild: discord.Guild = self.bot.get_guild(reaction.guild_id)
        channel: discord.TextChannel = guild.get_channel(reaction.channel_id)
        message: discord.Message = await channel.fetch_message(reaction.message_id)

        if user.bot: return
        await self.vm.on_reaction_add(reaction, emoji, message, user)


# Register module with bot
def setup(bot):
    bot.add_cog(Polls(bot))

