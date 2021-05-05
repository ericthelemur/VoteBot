import os
from datetime import datetime
from math import ceil
from typing import Optional, Union, Iterable

import discord
from discord import TextChannel
from discord.ext.commands import Bot, Context

from voting import voteDB
from voting.symbols import *

EmbedData = tuple[str, list[str], bool]

class StdVote:
    bot: Bot

    def __init__(self, bot):
        self.bot = bot
        self.remove_reacts = True

    async def on_react_add(self, reaction: discord.Reaction, user: discord.User, t: tuple) -> None:
        """
        Called on reaction add to a poll of this type. Entry point
        :param reaction: Reaction added
        :param user: User adding the reaction
        """

        if user.bot: return
        voteID, part, _, limit, _ = t
        msg: discord.Message = reaction.message
        em = str(reaction.emoji)

        # Process vote
        result = self.__react_action(user, em, voteID, part, limit)
        if self.remove_reacts: await msg.remove_reaction(reaction, user)

        # Send DM with confirmation
        if result:
            await self.__give_feedback(result, user, indexes.get(em, -1), voteID, limit)


    def __react_action(self, user: discord.User, em: str, voteID: int, part: int, limit: int) -> Union[str, tuple[str, list[int]]]:
        """
        Action to be taken when a reaction is added to a poll
        :param user: User voting
        :param em: Reaction (option) added
        :param voteID: ID of vote of message
        :param part: message part of the poll
        :param limit: maximum # of votes
        :return: result to give to feedback sender
        """

        if voteID is None: return ""
        if user.bot: return ""

        # If X, clear votes
        if em == clear_symbol:
            rem = voteDB.removeUserVote(voteID, user.id)
            return "clear votes", rem

        ind = indexes.get(em, -1)
        if not (part <= float(ind) / 20 < part + 1):
            return ""
        else:
            return self.__count_vote(ind, user, voteID, limit)


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
        r = voteDB.toggleUserVote(vid, user.id, ind, preference)
        return "added vote" if r else "removed vote"


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

        if isinstance(result, tuple) and result[0] == "clear votes":
            await user.dm_channel.send(f"Poll {vid}: Your votes have been cleared for:\n\t\t" +
                                       '\n\t\t'.join(f"{symbols[i]} **{options[i]}**" for i in result[1]))

        elif result == "added vote":
            await user.dm_channel.send(f"Poll {vid}: Counted your vote for {symbols[index]} **{options[index]}**")
        elif result == "removed vote":
            await user.dm_channel.send(f"Poll {vid}: Removed your vote for {symbols[index]} **{options[index]}**")

        elif result == "over limit":
            await user.dm_channel.send(
                f"Poll {vid}: Your vote for **{options[index]}** was **not counted**. You have voted for the **maximum of {limit}** choices. \n"
                f"\t\t**Remove a vote** before voting again: \n\t\tYour current choices are:\n\t\t\t" +
                '\n\t\t\t'.join(f"{symbols[i]} **{options[i]}**" for i, _ in voteDB.getUserVotes(vid, user.id))
                )



    async def create_vote(self, ctx: Context, args, desc=None, type=1) -> None:
        """
        Creates a vote, entry point.
        :param ctx: Context of vote (channel)
        :param args: args of command
        :param desc: Description of vote
        """
        # Extract values
        creator = ctx.author
        question = args.title
        options = args.options
        limit = args.limit
        num_wins = args.winners

        # Add to DB
        id = voteDB.addVote(creator, question, options, limit, ctx.guild, ctx.channel, 0, type, num_wins)

        if desc is None:
            desc = f"React to cast a vote for an option, you may vote for **{'multiple' if args.limit == 0 else args.limit}**. " \
                   f"Reacts will be removed once counted."
        else: desc = desc
        desc += f" End the vote with `{voteDB.getPrefix(ctx.guild.id)}close {id}`."

        # Post messages and add reactions, store stage to allow resume
        messages = await self.__post_vote(ctx, id, question, desc, options, creator.colour)
        voteDB.updateStage(id, 1)
        await self.__add_reactions(messages, options)
        voteDB.updateStage(id, 2)


    async def __post_vote(self, ctx: Context, vid: int, question: str, desc: str, options: list[str], colour) -> list[discord.Message]:
        """
        Posts the messages for a vote, 20 options per message, as that is discord's limit on reacts per message
        :param ctx: Context (channel) to send to
        :param vid: Vote ID
        :param question: Vote question
        :param desc: Vote description
        :param options: Vote options
        :param colour: Colour of vote embed
        """
        print("Posting")
        # Embed fields can be no longer than 1024 characters, so limit of 50 chars / option and 20 options per field
        lines = [f"{symbols[i]} {options[i]}" for i in range(len(options))] + [
            f"\n\n{clear_symbol} Clear all your votes"]

        messages = []

        # Add each 20 lines to new embed then post
        max_part = ceil(len(lines) / 20.0)
        for i in range(0, len(lines), 20):
            limit = min(i + 20, len(lines))
            d = desc if i == 0 else f"Part of poll `{vid}`. Split due to reaction count limit"
            embed = discord.Embed(title=f"Poll `{vid}`: {question} {f'part {i // 20 + 1}/{max_part}' if max_part > 1 else ''}",
                                  description=d,
                                  colour=colour, timestamp=datetime.utcnow())

            embed.add_field(name=f"Options" + ("" if i == 0 else "continued"), value="\n".join(lines[i:limit]),
                            inline=False)

            message = await ctx.send(embed=embed)
            messages.append(message)
            voteDB.addMessage(vid, message.id, i)
        return messages


    async def __add_reactions(self, messages: list[discord.Message], options: list[str]) -> None:
        """
        Adds the reactions to the vote messages, 20 per message due to discord limit
        :param messages: list of posted messages
        :param options: # of options
        """
        # Add reactions, discord has max of 20 per message
        for i0, m in enumerate(messages):
            limit = min(i0 * 20 + 20, len(options))
            for i in range(i0 * 20, limit):
                await m.add_reaction(symbols[i])

        # Add clear symbol
        msg = messages[len(options) // 20]
        await msg.add_reaction(clear_symbol)



    async def post_results(self, vid: int):
        """
        Posts results of a vote, entry point
        :param vid: vote ID
        """
        # Get information from DB and discord (messages, etc.)
        voteDB.updateStage(vid, -1)

        messages = voteDB.getMessages()
        for vid, gid, cid, mid in messages:
            guild: discord.Guild = self.bot.get_guild(gid)
            channel: TextChannel = guild.get_channel(cid)
            message: discord.Message = await channel.fetch_message(mid)
            await message.clear_reactions()

        uid, question, gid, cid, type, num_win = voteDB.getVote(vid)
        fields = self.__make_results(vid, num_win)

        guild: discord.Guild = self.bot.get_guild(gid)
        channel: TextChannel = guild.get_channel(cid)
        creator = guild.get_member(uid)

        # If first field is file (used in STV export, etc.), extract it
        file: Optional[discord.File] = None
        if isinstance(fields[0], discord.File):
            file = fields[0]
            fields = fields[1:]

        # Split fields into 20 entries per field, so do not go over limit
        split_fields = []
        for field in fields:
            title, lines, inline = field
            max_part = ceil(len(lines) / 20.0)

            # Split field
            split_fields.append((title, "\n".join(lines if len(lines) < 20 else lines[:20]), inline))
            for i in range(20, len(lines), 20):
                limit = min(i + 20, len(lines))
                split_fields.append((title + f" part {i // 20 + 1}/{max_part}", "\n".join(lines[i:limit]), inline))

        # Create embeds, split if embed ends up being too long, shouldn't be necessary with option length limit
        embed = discord.Embed(title="Results: " + question, colour=creator.colour, timestamp=datetime.utcnow())
        msg_length = 0
        part = 1
        for n, v, i in split_fields:
            msg_length += len(v)
            if msg_length > 4000:   # If too long, send and reset embed
                await channel.send(embed=embed)
                part += 1
                embed = discord.Embed(title=f"Results part{part}: " + question, colour=creator.colour,
                                      timestamp=datetime.utcnow())
            embed.add_field(name=n, value=v, inline=i)

        # If file, attach it and delete temp
        if file:
            await channel.send(embed=embed, file=file)
            os.remove(os.path.join(TEMP_DATA_PATH, file.filename))
        else:
            await channel.send(embed=embed)


    def __make_results(self, vid: int, num_win: int) -> list[Union[discord.File, EmbedData]]:
        """
        Makes result list for vote
        :param vid: Vote ID
        :return: List of embed parts
        """
        votes = dict(voteDB.getUserVoteCount(vid))
        options = [k for k in votes.keys()]

        sections = [self.__top_n_results(num_win, options, votes, "Winners")]
        if num_win < 5: sections.append(self.__top_n_results(5, options, votes))
        sections.append(self.__list_results(options, range(len(options)), votes))

        return sections


    @staticmethod
    def __list_results(options: list[str], order: Union[Iterable[int], list[int]], votes: dict[int, int], title="Results") -> EmbedData:
        """
        Creates embed parts that list options in order
        :param options: Options to list
        :param order: Order of options to display
        :param title: Title of embed
        :param votes: Source votes to include
        :return: Embed parts
        """
        start_msg = ""
        if len(options) > 20:  # If long, only display non-zero results
            order = [p for p in order if votes[p] > 0]
            start_msg = "As a large number of results, omitting options with zero votes\n"
            if len(order) == 0: return title, [start_msg] + ["All options received 0 votes."], False

        return title, [start_msg] + [f"{symbols[i]} **{options[i]}**: **{votes[i]}** votes" for i in order], False


    @staticmethod
    def __top_n_results(n: int, options: list[str], votes: dict[int, int], title=None) -> EmbedData:
        """
        Gets the top n results of options by votes
        :param n: number of top results to get
        :param options: options to pick from
        :param votes: vote data to sort by
        :return: Embed parts
        """
        print("voteOps", options)
        if title is None: title = f"Top {n}"
        options = options.copy()
        options.sort(key=lambda x: -votes.get(x, 0))

        picked = []
        if n < len(options):
            threshold = -1
            for op in options:
                if len(picked) <= 5:
                    picked.append(op)
                    threshold = votes.get(op, 0)
                elif votes.get(op, 0) == threshold:
                    picked.append(op)
                else: break
        else: picked = options

        return StdVote.__list_results(options, picked, votes, title)