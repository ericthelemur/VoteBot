from discord.ext import commands
from discord.ext.commands import Context

from voting import vote
from voting.vote import symbols, running_votes
from parsers import *


# Main poll class, mainly a wrapper around Vote
class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="createpoll", aliases=["poll", "secretpoll"], help=poll_parser.format_help())
    async def create_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):  # Extra checks past the parser's basic ones. These are caught and forwarded in run_parser
                if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                for op in args.options:
                    if len(op) > 50: raise argparse.ArgumentError(opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

            args = run_parser(poll_parser, options, extra_checks)
            # Send feedback or run vote
            if isinstance(args, str): await ctx.send(args)
            else:
                v = vote.Vote(ctx, self.bot, args)
                await v.run()

        # Catch any exception, to ensure the bot continues running for other votes
        # and to give error message due to error messages in async blocks not being reported otherwise
        except Exception as e:
            print(e)
            raise e


    @commands.command(name="quickpoll", aliases=["qpoll"], help=("Runs a quick poll.\n" + vis_poll_parser.format_help()))
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
                v = vote.QuickPoll(ctx, args)
                await v.run()

        # Catch any exception, to ensure the bot continues running for other votes
        # and to give error message due to error messages in async blocks not being reported otherwise
        except Exception as e:
            print(e)
            raise e


    #
    # @commands.command(name="stvpoll", help=("Runs a STV poll.\n" + stv_parser.format_help()))
    # async def create_stv_poll(self, ctx: Context, *options):
    #     try:
    #         print("Parsing args")
    #
    #         def extra_checks(args):
    #             if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(stv_opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
    #             if args.winners <= 0: raise argparse.ArgumentError(stv_win_arg, f"STV cannot select less than 1 winner.")
    #
    #             for op in args.options:
    #                 if len(op) > 50: raise argparse.ArgumentError(stv_opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")
    #
    #         args = run_parser(stv_parser, options, extra_checks)
    #         if isinstance(args, str): await ctx.send(args)
    #         else:
    #             v = vote.STVPoll(ctx, self.bot, args)
    #             await v.run()
    #
    #     except Exception as e:
    #         print(e)
    #         raise e


    @commands.command(name="close", aliases=["closepoll", "closevote"], help="Ends a poll with ID `pid`")
    async def close_poll(self, ctx: Context, pid: int):
        print("Closing", pid)

        if pid in running_votes:    # Finds poll in polls
            v = running_votes[pid]
            if ctx.author == v.creator:   # Has perms
                v.end()

            else: await ctx.send("You are not allowed to cancel this poll")
        else: await ctx.send("This poll does not exist")

    # TODO Get vote # cmd
    # @commands.command(name="dump")
    # async def dump(self, ctx: Context):
    #     try:
    #         print("Dumping")
    #         print(running_votes)
    #         for vote in running_votes.values():
    #             print({"id": vote.id,
    #                    "guild": vote.ctx.guild.id, "channel": vote.ctx.channel.id, "messages": [msg.id for msg in vote.messages],
    #                    "options": vote.options})
    #     except Exception as e:
    #         print(e)

# Register module with bot
def setup(bot):
    bot.add_cog(Polls(bot))
