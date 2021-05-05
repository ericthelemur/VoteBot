import os
from collections import defaultdict, Counter
from datetime import datetime
from math import ceil
from typing import Optional, Union, Iterable

import discord
from discord import TextChannel
from discord.ext.commands import Bot, Context

from voting import voteDB, stv
from voting.symbols import *

from voting.vote_types.std_vote import EmbedData, StdVote


class STVVote(StdVote):
    async def create_vote(self, ctx: Context, args, desc=None, type=2) -> None:
        if desc != None:
            f"React to cast a vote for an option, **in order of your preference**. "
            f"You may vote for **{'multiple' if args.limit == 0 else args.limit}**. "
            f"Reacts will be removed once counted."
        await super(STVVote, self).create_vote(ctx, args, desc, type=type)

    def __count_vote(self, ind: int, user: discord.User, vid: int, limit: int) -> str:
        """
        Counts a vote for ind from user
        :param ind: Index of option chosen
        :param user: User selected
        :param vid: id of vote
        :param limit: vote limit
        :return: feedback result
        """
        users_votes = voteDB.getUserVoteCount(vid, uid=user.id)
        if limit and users_votes >= limit:
            return "over limit"

        preference = voteDB.getUserNextPref(vid, user.id)
        r = voteDB.prefUserVote(vid, user.id, ind, preference)
        return "added vote" if r else "already counted"

    async def __give_feedback(self, result: str, user: discord.User, index: Union[int, list[int]], vid: int, limit: int) -> None:
        """
        Sends DM to user with result of reaction
        :param result: str with result of reaction
        :param user: user to send DM to
        :param index: index of option, -1 if wrong (ignored) or index of choice. If clear, list of indexes removed
        :param vid: vote ID
        :param limit: vote limit
        """
        await user.create_dm()
        print(f"Sending DM for {result} to {user}")

        options = [x[1] for x in voteDB.getOptions(vid)]
        user_votes = [x[0] for x in sorted(voteDB.getUserVotes(vid, user.id), key=lambda x: x[1])]

        if result == "added vote":
            await user.dm_channel.send(f"Poll {vid}: Counted your vote for {symbols[index]} **{options[index]}** at position {user_votes.index(index)+1}")
        elif result == "removed vote":
            await user.dm_channel.send(f"Poll {vid}: Removed your vote for {symbols[index]} **{options[index]}**")
        elif result == "over limit":
            await user.dm_channel.send(f"Poll {vid}: Your vote for **{options[index]}** was **not counted**. "
                                       f"You have voted for the **maximum of {limit}** choices. \n"
                                       f"\t\t**Remove a vote** before voting again: \n\t\tYour current choices are:\n\t\t\t" +
                                       '\n\t\t\t'.join(f"{symbols[i]} **{options[i]}**" for i in user_votes)
                                       )
        elif result == "clear votes":
            await user.dm_channel.send(f"Poll {vid}: Your votes have been cleared for:\n\t\t" +
                                       '\n\t\t'.join(f"{symbols[i]} **{options[i]}**" for i in index))
        elif result == "already counted":
            await user.dm_channel.send(f"Poll {vid}: You have **already voted** for {options[index]} option as preference #{user_votes.index(index)+1}. "
                                       f"To change your ordering, **clear votes** and enter your updated order.\n"
                                       f"your current preferences are:\n\t\t" +
                                       '\n\t\t'.join(f"{i+1}: {symbols[c]} **{options[c]}**" for i, c in enumerate(user_votes)))

    def __make_results(self, vid: int, num_win: int) -> list[Union[discord.File, EmbedData]]:
        """
        Makes result list for vote
        :param vid: Vote ID
        :return: List of embed parts
        """

        # Get votes from DB
        votes = voteDB.getUserVotes(vid)

        # Group by user in dict
        user_prefs = defaultdict(dict)
        for uid, choice, pref in votes:
            user_prefs[uid][pref] = choice

        # Convert dict to list
        counts = Counter()
        first_pref = Counter()
        for uid, ord_dict in user_prefs:
            uv = []
            for k in sorted(ord_dict.keys()):
                for i in range(len(uv), k, 1):
                    uv.append(0)
                uv[k] = ord_dict[k]
            counts[tuple(uv)] += 1
            first_pref[uv[0]] += 1

        options = voteDB.getOptions(vid)
        indexes = list(range(len(options)))
        print("Votes parcelled ", counts, first_pref)
        vote = stv.STV(indexes.copy(), counts, num_win)

        # Make file of votes
        path = os.path.join(TEMP_DATA_PATH, f"{vid}.votes")
        with open(path, "w") as dump_file:
            for k, v in vote.preferences.items():
                print(f"{v}: {k}", file=dump_file)

        winners = vote.run()
        print("STV Run, winners are", winners)

        first_prefs = indexes.copy()
        first_prefs.sort(key=lambda x: -first_pref[x])

        return [discord.File(path), ("STV Winners", [f"{symbols[i]} **{options[i]}**" for i in winners] if winners else ["No winners."], False),
                self.__list_results(options, first_prefs, first_pref, "First Preference Votes")]

        # TODO Construct vote tuples
        # counts = Counter()
        # first_pref_votes = Counter()
        #
        # for uv in self.votes.user_votes.values():
        #     print(uv)
        #     counts[tuple(uv)] += 1
        #     first_pref_votes[uv[0]] += 1
        #
        # indexes = list(range(len(self.options)))
        # print("Votes parcelled ", counts, first_pref_votes)
        # vote = stv.STV(indexes.copy(), counts, self.winners)
        #
        # # Make file of votes
        # path = os.path.join(TEMP_DATA_PATH, f"{self.id}.votes")
        # with open(path, "w") as dump_file:
        #     for k, v in vote.preferences.items():
        #         print(f"{v}: {k}", file=dump_file)
        #
        # winners = vote.run()
        # print("STV Run, winners are", winners)
        #
        # first_prefs = indexes.copy()
        # first_prefs.sort(key=lambda x: -first_pref_votes[x])
        #
        # return [discord.File(path), ("STV Winners", [f"{symbols[i]} **{self.options[i]}**" for i in winners] if winners else ["No winners."], False),
        #         self.list_results(first_prefs, "First Preference Votes", votes=first_pref_votes)]