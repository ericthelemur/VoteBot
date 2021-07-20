import os
from datetime import datetime
from math import ceil
from typing import Optional, Union, Iterable

import discord
from discord import TextChannel
from discord.ext.commands import Bot, Context

from voting import voteDB
from voting.symbols import *
from voting.voteDB import OverLimitException

EmbedData = tuple[str, list[str], bool]


class StdVote:
    bot: Bot

    def __init__(self, bot):
        self.bot = bot
        self.remove_reactions = True
        self.clear = True
        self.order_text = "Any"
        self.close_desc = True

    async def on_react_add(self, emoji: str, msg: discord.Message, user: discord.Member, t: tuple) -> None:
        """
        Called on reaction add to a poll of this type. Entry point
        :param reaction: Reaction added
        :param user: User adding the reaction
        """

        if user.bot: return
        voteID, part, _, limit, _ = t

        # Process vote
        result = self.react_action(user, emoji, voteID, part, limit, msg)
        if self.remove_reactions or not result: await msg.remove_reaction(emoji, user)

        # Send DM with confirmation
        if result:
            await self.give_feedback(result, user, indexes.get(emoji, -1), voteID, limit)


    async def on_react_remove(self, emoji: str, msg: discord.Message, user: discord.Member, t: tuple) -> None:
        pass


    def react_action(self, user: discord.Member, em: str, voteID: int, part: int, limit: int, msg: discord.Message) -> Union[str, tuple[str, list[int]]]:
        """
        Action to be taken when a reaction is added to a poll
        :param msg:
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
        if not (part <= ind < part + 20):
            return ""
        else:
            return self.count_vote(ind, user, voteID, limit)


    def count_vote(self, ind: int, user: discord.Member, vid: int, limit: int) -> str:
        """
        Counts a vote for ind from user
        :param ind: Index of option chosen
        :param user: User selected
        :param vid: id of vote
        :param limit: vote limit
        :return: feedback result
        """
        preference = voteDB.getUserNextPref(vid, user.id)
        try:
            r = voteDB.toggleUserVote(vid, user.id, ind, preference, limit)
            return "added vote" if r else "removed vote"
        except OverLimitException:
            return "over limit"


    async def give_feedback(self, result, user: discord.Member, index, vid, limit):
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



    async def create_vote(self, ctx: Context, args, desc=None, type=1, title_pre: str = "Anonymous Poll") -> None:
        """
        Creates a vote, entry point.
        :param ctx: Context of vote (channel)
        :param args: args of command
        :param desc: Description of vote
        """
        # Extract values
        creator = ctx.author
        title = args.title
        options = args.options
        limit = args.limit
        num_wins = args.winners

        # Add to DB
        id, title = voteDB.addVote(creator, title, options, limit, ctx.guild, ctx.channel, 0, type, num_wins, title_pre)

        if desc is None:
            desc = self.vote_summary(args)
        else: desc = desc
        if self.close_desc: desc += f" End the vote with `{voteDB.getPrefix(ctx.guild.id)}close {id}`."

        # Post messages and add reactions, store stage to allow resume
        messages = await self.post_vote(ctx, id, title, desc, options, creator.colour)
        voteDB.updateStage(id, 1)
        await self.add_reactions(messages, options)
        voteDB.updateStage(id, 2)


    def vote_summary(self, args):
        return f"Votes: **{'Hidden' if self.remove_reactions else 'Visible'}** Order: **{self.order_text}** Vote Limit: **{str(args.limit) if args.limit > 0 else 'None'}** Winners: **{args.winners}**\n"\


    async def post_vote(self, ctx: Context, vid: int, title: str, desc: str, options: list[str], colour) -> list[discord.Message]:
        """
        Posts the messages for a vote, 20 options per message, as that is discord's limit on reacts per message
        :param ctx: Context (channel) to send to
        :param vid: Vote ID
        :param title: Vote question
        :param desc: Vote description
        :param options: Vote options
        :param colour: Colour of vote embed
        """
        print("Posting")
        # Embed fields can be no longer than 1024 characters, so limit of 50 chars / option and 20 options per field
        lines = [f"{symbols[i]} {options[i]}" for i in range(len(options))]
        if self.clear and self.remove_reactions: lines.append(f"\n\n{clear_symbol} Clear all your votes")

        messages = []

        # Add each 20 lines to new embed then post
        max_part = ceil(len(lines) / 20.0)
        for i in range(0, len(lines), 20):
            limit = min(i + 20, len(lines))
            d = desc if i == 0 else f"Part of poll `{vid}`. Split due to reaction count limit"
            embed = discord.Embed(title=f"{title} {f'part {i // 20 + 1}/{max_part}' if max_part > 1 else ''}",
                                  description=d,
                                  colour=colour, timestamp=datetime.utcnow())

            embed.add_field(name=f"Options" + ("" if i == 0 else "continued"), value="\n".join(lines[i:limit]),
                            inline=False)

            message = await ctx.send(embed=embed)
            messages.append(message)
            voteDB.addMessage(vid, message.id, i)
        return messages


    async def add_reactions(self, messages: list[discord.Message], options: list[str]) -> None:
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

        if self.clear:
            # Add clear symbol
            msg = messages[len(options) // 20]
            await msg.add_reaction(clear_symbol)



    async def post_results(self, vid: int):
        """
        Posts results of a vote, entry point
        :param vid: vote ID
        """
        # Get information from DB and discord (messages, etc.)
        print("Making results of vote", vid)
        messages = voteDB.getMessages(vid)
        for gid, cid, mid in messages:
            guild: discord.Guild = self.bot.get_guild(gid)
            channel: TextChannel = guild.get_channel(cid)
            message: discord.Message = await channel.fetch_message(mid)
            await message.clear_reactions()
            print("Clearing reactions from msg", mid)

        uid, question, gid, cid, type, num_win = voteDB.getVote(vid)

        voteDB.updateStage(vid, -1)
        fields = self.make_results(vid, num_win)

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
        embed = discord.Embed(title="Results of " + question, colour=creator.colour, timestamp=datetime.utcnow())
        msg_length = 0
        part = 1
        for n, v, i in split_fields:
            msg_length += len(v)
            if msg_length > 4000:   # If too long, send and reset embed
                await channel.send(embed=embed)
                part += 1
                embed = discord.Embed(title=f"Results part {part} of  " + question, colour=creator.colour,
                                      timestamp=datetime.utcnow())
            embed.add_field(name=n, value=v, inline=i)

        # If file, attach it and delete temp
        if file: await channel.send(embed=embed, file=file)
        else: await channel.send(embed=embed)

        voteDB.removeVote(vid)


    async def halt(self, vid: int):
        """
        Ends vote without results
        :param vid: vote ID
        """
        # Get information from DB and discord (messages, etc.)
        print("Halting vote", vid)
        messages = voteDB.getMessages(vid)
        for gid, cid, mid in messages:
            guild: discord.Guild = self.bot.get_guild(gid)
            channel: TextChannel = guild.get_channel(cid)
            message: discord.Message = await channel.fetch_message(mid)
            # await message.clear_reactions()
            await message.delete()

        uid, question, gid, cid, type, num_win = voteDB.getVote(vid)

        voteDB.updateStage(vid, -1)

        guild: discord.Guild = self.bot.get_guild(gid)
        channel: TextChannel = guild.get_channel(cid)

        voteDB.removeVote(vid)

        await channel.send(f"Vote {vid} halted.")



    def make_results(self, vid: int, num_win: int) -> list[Union[discord.File, EmbedData]]:
        """
        Makes result list for vote
        :param vid: Vote ID
        :return: List of embed parts
        """
        votes = dict(voteDB.getUserVoteCount(vid))
        options = ["" for _ in range(len(votes))]
        for i, text in voteDB.getOptions(vid):
            options[i] = text

        sections = [StdVote.top_n_results(num_win, options, votes, title="Winners")]
        if num_win < 5: sections.append(StdVote.top_n_results(5, options, votes))
        sections.append(StdVote.list_results(options, list(range(len(options))), votes))

        return sections


    @staticmethod
    def list_results(options: list[str], order: list[int], votes: dict[int, int], title="Results") -> EmbedData:
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

        print(order, options, votes)
        return title, [start_msg] + [f"{symbols[i]} **{options[i]}**: **{votes[i]}** votes" for i in order], False


    @staticmethod
    def top_n_results(n: int, options: list[str], votes: dict[int, int], title=None) -> EmbedData:
        """
        Gets the top n results of options by votes
        :param n: number of top results to get
        :param options: options to pick from
        :param votes: vote data to sort by
        :return: Embed parts
        """

        order = list(votes.keys())
        order.sort(key=lambda x: -votes.get(x, 0))

        picked = order[:n]
        for i in range(len(picked)-1, -1, -1):
            if votes.get(picked[i], 0) == 0: picked.pop(i)

        limit = votes.get(picked[-1], 0)
        for op in order[n:]:
            if votes.get(op, 0) >= limit:
                picked.append(op)

        n = min(len(options), n)
        if title is None: title = f"Top {n}"

        return StdVote.list_results(options, picked, votes, title)
