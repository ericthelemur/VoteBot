from typing import Union

from voting.vote_types.std_vote import StdVote

import discord
from discord.ext.commands import Context

from voting.symbols import *


class VisibleVote(StdVote):
    def __init__(self, bot):
        super().__init__(bot)
        self.remove_reactions = False
        self.clear = False

    async def on_react_add(self, emoji: str, msg: discord.Message, user: discord.Member, t: tuple) -> None:
        if user.bot: return
        voteID, part, _, limit, _ = t

        # Process vote
        result = self.react_action(user, emoji, voteID, part, limit, msg)
        if result == "over limit" or not result: await msg.remove_reaction(emoji, user)

        # Send DM with confirmation
        if result:
            await self.give_feedback(result, user, indexes.get(emoji, -1), voteID, limit)


    def react_action(self, user: discord.Member, em: str, voteID: int, part: int, limit: int, msg) -> Union[str, tuple[str, list[int]]]:
        if voteID is None: return ""
        if user.bot: return ""

        ind = indexes.get(em, -1)
        if not (part <= ind < part + 20):
            return ""
        else:
            return self.count_vote(ind, user, voteID, limit)


    async def on_react_remove(self, emoji: str, msg: discord.Message, user: discord.Member, t: tuple) -> None:
        return await self.on_react_add(emoji, msg, user, t)


    async def create_vote(self, ctx: Context, args, desc=None, type=0, title_pre="Visible Poll") -> None:
        await super().create_vote(ctx, args, desc, type=type, title_pre=title_pre)

