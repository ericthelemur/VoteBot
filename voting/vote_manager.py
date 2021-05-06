from datetime import datetime

import discord
from discord.ext.commands import Bot

from voting import voteDB
from voting.symbols import *
from voting.vote_types.std_vote import StdVote
from voting.vote_types.stv_vote import STVVote


class VoteManager:
    bot: Bot

    def __init__(self, bot):
        self.bot = bot


    async def quick_poll(self, ctx, args):
        qp = QuickPoll(ctx, args)
        messages = await qp.post_poll()
        await qp.add_reactions(messages)


    async def std_vote(self, ctx, args):
        sv = StdVote(self.bot)
        await sv.create_vote(ctx, args)


    async def stv_vote(self, ctx, args):
        stv = STVVote(self.bot)
        await stv.create_vote(ctx, args)


    async def on_reaction_add(self, r_event: discord.RawReactionActionEvent, emoji: str, message: discord.Message, user: discord.User):
        t = voteDB.getMsgVote(r_event.message_id)
        if t is None: return
        vid, _, type, _, stage = t
        if stage < 0: return

        v = None
        if type == 1: v = StdVote(self.bot)
        elif type == 2: v = STVVote(self.bot)
        else: return

        if v: await v.on_react_add(emoji, message, user, t)


    async def close(self, vid):
        _, _, _, _, type, _ = voteDB.getVote(vid)

        v = None
        if type == 1: v = StdVote(self.bot)
        elif type == 2: v = STVVote(self.bot)

        if v: await v.post_results(vid)


class QuickPoll:
    def __init__(self, ctx, args, desc=None):
        self.ctx = ctx
        # running_votes[self.id] = self

        self.creator = ctx.author
        self.question = args.title
        self.options = args.options
        self.react_count = len(self.options)

        if desc is None:
            self.desc = f"React to cast a vote for an option, you may vote for **multiple**. Votes will be visible."
        else:
            self.desc = desc

        print("Created Quick poll")

    async def post_poll(self):
        print("Posting")

        # Create poll embed
        embed = discord.Embed(title=f"Quick Poll: {self.question}", description=self.desc,
                              colour=self.creator.colour, timestamp=datetime.utcnow())

        # If no options given, default to thumbs up and down
        if self.options:
            fields = [(
                      "Options", "\n".join(f"{symbols[i]} {self.options[i]}" for i in range(len(self.options))),
                      False)]
        else:
            fields = [("Options", "\n".join(f"{s} {o}" for s, o in (("👍", "Yes"), ("👎", "No"))), False)]

        for n, v, i in fields:
            embed.add_field(name=n, value=v, inline=i)

        # Send messages
        message = await self.ctx.send(embed=embed)
        messages = [message]
        for i in range(20, self.react_count, 20):
            messages.append(await self.ctx.send("_ _"))  # Italic space appears as empty message
        print("Sent poll")
        return messages

    async def add_reactions(self, messages, start_index=0):
        if self.options:
            # Add reactions, discord has max of 20 per message
            for i0 in range(start_index, len(messages)):
                m = messages[i0]
                limit = min(i0 * 20 + 20, len(self.options))
                for i in range(i0 * 20, limit):
                    await m.add_reaction(symbols[i])
        else:
            m = messages[0]
            for s in ("👍", "👎"):
                await m.add_reaction(s)

        print("Added reactions")
