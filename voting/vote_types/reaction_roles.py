from typing import Union

from voting import voteDB
from voting.vote_types.std_vote import StdVote

import discord
from discord.ext.commands import Context

from voting.symbols import *


class ReactionRoles(StdVote):
    def __init__(self, bot):
        super().__init__(bot)
        self.clear = False
        self.close_desc = False


    def count_vote(self, ind: int, user: discord.Member, vid: int, limit: int) -> str:
        role_name = voteDB.getOptions(vid)[ind]
        # print(role_name[1].lower(), [r.name.lower() for r in user.roles])
        role: discord.Role = next((r for r in user.roles if role_name[1].lower() == r.name.lower()), None)
        if not role: return "added vote"
        else: return "removed vote"


    async def give_feedback(self, result, user: discord.Member, index, vid, limit):
        await user.create_dm()
        print(f"Sending DM for {result} to {user}")

        options = [x[1] for x in voteDB.getOptions(vid)]

        if isinstance(result, tuple) and result[0] == "clear votes":
            await user.dm_channel.send(f"Reaction Action {vid}: Your roles have been cleared for:\n\t\t" +
                                       '\n\t\t'.join(f"{symbols[i]} **{options[i]}**" for i in result[1]))

        elif result == "added vote":
            role_name = voteDB.getOptions(vid)[index]
            role: discord.Role = next((r for r in user.guild.roles if role_name[1].lower() == r.name.lower()), None)
            await user.add_roles(role, atomic=True)
            await user.dm_channel.send(f"Reaction Action {vid}: Added role {symbols[index]} **{options[index]}**")

        elif result == "removed vote":
            role_name = voteDB.getOptions(vid)[index]
            role: discord.Role = next((r for r in user.roles if role_name[1].lower() == r.name.lower()), None)
            await user.remove_roles(role, atomic=True)
            await user.dm_channel.send(f"Reaction Action {vid}: Removed role {symbols[index]} **{options[index]}**")

        elif result == "over limit":
            await user.dm_channel.send(
                f"Poll {vid}: Your vote for **{options[index]}** was **not counted**. You have voted for the **maximum of {limit}** choices. \n"
                f"\t\t**Remove a vote** before voting again: \n\t\tYour current choices are:\n\t\t\t" +
                '\n\t\t\t'.join(f"{symbols[i]} **{options[i]}**" for i, _ in voteDB.getUserVotes(vid, user.id))
            )


    async def create_vote(self, ctx: Context, args, desc=None, type=100, title_pre="Reaction Roles") -> None:
        await super().create_vote(ctx, args, "", type=type, title_pre=title_pre)

