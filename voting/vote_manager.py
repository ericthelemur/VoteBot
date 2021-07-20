import discord
from discord.ext.commands import Bot, Context

from voting import voteDB
from voting.vote_types.reaction_roles import ReactionRoles
from voting.vote_types.std_vote import StdVote
from voting.vote_types.stv_vote import STVVote
from voting.vote_types.vis_vote import VisibleVote


class VoteManager:
    bot: Bot

    def __init__(self, bot):
        self.bot = bot

    def get_vote_type(self, t):
        if t == 0: return VisibleVote(self.bot)
        elif t == 1: return StdVote(self.bot)
        elif t == 2: return STVVote(self.bot)
        elif t == 100: return ReactionRoles(self.bot)
        else: return None


    async def visible_poll(self, ctx: Context, args):
        vv = VisibleVote(self.bot)
        await vv.create_vote(ctx, args)


    async def std_vote(self, ctx, args):
        sv = StdVote(self.bot)
        await sv.create_vote(ctx, args)


    async def stv_vote(self, ctx, args):
        stv = STVVote(self.bot)
        await stv.create_vote(ctx, args)


    async def reaction_roles(self, ctx, args):
        rr = ReactionRoles(self.bot)
        await rr.create_vote(ctx, args)



    async def on_reaction_add(self, r_event: discord.RawReactionActionEvent, emoji: str, message: discord.Message, user: discord.Member):
        t = voteDB.getMsgVote(r_event.message_id)

        if t is None: return
        vid, _, type, _, stage = t
        if stage < 0: return

        v = self.get_vote_type(type)
        print(t, v)
        if v: await v.on_react_add(emoji, message, user, t)

    async def on_reaction_remove(self, r_event: discord.RawReactionActionEvent, emoji: str, message: discord.Message, user: discord.Member):
        t = voteDB.getMsgVote(r_event.message_id)
        if t is None: return
        vid, _, type, _, stage = t
        if stage < 0: return

        v = self.get_vote_type(type)
        if v: await v.on_react_remove(emoji, message, user, t)


    async def close(self, vid):
        _, _, _, _, type, _ = voteDB.getVote(vid)
        v = self.get_vote_type(type)

        if v: await v.post_results(vid)


    async def halt(self, vid):
        _, _, _, _, type, _ = voteDB.getVote(vid)
        v = self.get_vote_type(type)

        if v: await v.halt(vid)

