import asyncio
from datetime import datetime
import random
import typing
from collections import defaultdict, Counter

import discord

import stv

clear_symbol = "❌"
# List of symbols to use in reacts. Discord formats of these strangely
symbols = ["⚪", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⬜", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫", "🤍", "❤️", "🧡", "💛", "💚", "💙", "💜", "🤎",
           "🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸", "🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿", "1️⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟",
           "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋", "🐌", "🪱", "🐞",
           "🪳", "🪲", "🐢", "🦎", "🦕", "🐙", "🦑", "🦀", "🐠", "🐟", "🐬", "🦈", "🦓", "🐘", "🐪", "🦒", "🦚", "🦜", "🦢", "🦩", "🦔",
           "🌍", "🌕", "🪐", "⭐", "⚡", "💥", "🔥", "🌈", "☀️", "☁️", "❄️", "💨", "💧",
           "🌲", "🌳", "🌴", "🌿", "🍁", "🍄", "🐚", "🌾", "🌹", "🍏", "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🫐", "🍓", "🍈", "🍒", "🍍",
           "🥝", "🍆", "🥕", "🧄", "🥐", "🍞", "🧀", "🥞", "🥓", "🥩", "🍗", "🌭", "🍔", "🍟", "🍕", "🍨", "🍬", "🍫", "🍿", "🍩", "☕", "🍺",
           "⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🪃", "🏓", "🏏", "🪁", "🛹",
           "🏆", "🥇", "🥈", "🥉", "🏅", "🎨", "🎬", "🥁", "🪘", "🎷", "🎺", "🎸", "🪗", "🎲", "♟️", "🎯", "🎳", "🧩",
           "🚗", "🚕", "🚙", "🚎", "🏎️", "🚑", "🚜", "🚨", "🚆", "✈️", "🚀", "🛸", "🚁", "⛵", "🚢", "⛽", "🗺️", "⛱️", "⛺", "🏛️", "⛩️", "🌠", "🎇", "🏙️", "🌉",
           "💻", "🖨️", "🖱️", "📀", "☎️", "🎙️", "⏰", "⌛", "💡", "🕯️", "🪙", "💎", "⚖️", "🔧", "🧱", "🧲", "🔫", "🛡️", "✉️", "📒", "📕", "📗", "📘", "📙", "📎", "🖌️", "📝", "🔒", "🔶", "🔷", "🔈", "🔔",
           ]

indexes = {symbols[i]: i for i in range(len(symbols))}

running_votes = dict()


# Basic poll with visible results, no behaviour on closing
class QuickPoll:
    def __init__(self, ctx, args, desc=None):
        self.ctx = ctx
        self.id = Vote.pick_id()
        print("Creating quick poll", self.id)
        running_votes[self.id] = self

        self.creator = ctx.author
        self.question = args.title

        self.options = args.options

        self.react_count = len(self.options)

        if desc is None:
            self.desc = f"React to cast a vote for an option, you may vote for **multiple**. Votes will be visible."
        else: self.desc = desc

        print("Created poll", self.id)

    async def run(self):
        messages = await self.post_poll()
        await self.add_reactions(messages)

        running_votes.pop(self.id)
        print(f"Poll {self.id} over")


    async def post_poll(self):
        print("Posting")

        # Create poll embed
        embed = discord.Embed(title=f"Poll `{self.id}`: {self.question}", description=self.desc,
                              colour=self.creator.colour, timestamp=datetime.utcnow())

        # If no options given, default to thumbs up and down
        if self.options:
            fields = [("Options", "\n".join(f"{symbols[i]} {self.options[i]}" for i in range(len(self.options))), False)]
        else: fields = [("Options", "\n".join(f"{s} {o}" for s, o in (("👍", "Yes"), ("👎", "No"))), False)]

        for n, v, i in fields:
            embed.add_field(name=n, value=v, inline=i)

        # Send messages
        message = await self.ctx.send(embed=embed)
        messages = [message]
        for i in range(20, self.react_count, 20):
            messages.append(await self.ctx.send("_ _"))  # Italic space appears as empty message
        print("Sent poll")
        return messages


    async def add_reactions(self, messages):
        if self.options:
            # Add reactions, discord has max of 20 per message
            for i0 in range(len(messages)):
                m = messages[i0]
                limit = min(i0 * 20 + 20, len(self.options))
                for i in range(i0 * 20, limit):
                    await m.add_reaction(symbols[i])
        else:
            m = messages[0]
            for s in ("👍", "👎"):
                await m.add_reaction(s)

        print("Added reactions")



# Standard hidden vote, results only visible on closing
class Vote:
    def __init__(self, ctx, bot, args, desc=None):
        self.running = True
        self.ctx = ctx
        self.bot = bot
        self.id = Vote.pick_id()
        print("Creating standard poll", self.id)
        running_votes[self.id] = self

        self.creator = ctx.author
        self.question = args.title
        self.options = args.options
        self.react_count = len(self.options)+1
        self.limit = args.limit

        if desc is None:
            self.desc = f"React to cast a vote for an option, you may vote for **{'multiple' if args.limit == 0 else args.limit}**. " \
                        f"Reacts will be removed once counted. End the vote with `!close {self.id}`."
        else: self.desc = desc

        self.votes = self.make_votes()

        self.tasks = []
        print("Created poll", self.id)

    async def run(self):
        messages = await self.post_poll()
        self.create_tasks(messages)
        await self.add_reactions(messages)

        if self.running:
            # Run react tasks
            try:
                await asyncio.gather(*self.tasks)
            except CancelException:
                pass

        print("Vote ended")

        # Clean up poll
        for msg in messages:
            await msg.clear_reactions()  # Keep first message around, just remove reactions to signify closed
        # for msg in messages[1:]:             # Delete blank messages: only exist to support >20 options
        #     await msg.delete()

        await self.post_results()
        print(f"Poll {self.id} over")


    async def post_poll(self):
        print("Posting")

        # Create poll embed

        # Embed fields can be no longer than 1024 characters, so limit of 50 chars / option and 20 options per field
        lines = [f"{symbols[i]} {self.options[i]}" for i in range(len(self.options))] + [f"\n\n{clear_symbol} Clear all your votes"]

        embed = discord.Embed(title=f"Poll `{self.id}`: {self.question}", description=self.desc,
                              colour=self.creator.colour, timestamp=datetime.utcnow())
        embed.add_field(name="Options", value="\n".join(lines if len(lines) < 20 else lines[:20]), inline=False)
        embeds = [embed]

        for i in range(20, len(lines), 20):
            limit = min(i + 20, len(lines))
            embed = discord.Embed(title=f"Poll `{self.id}`: {self.question} part {i//20+1}/{(len(lines)+19) // 20}", description=f"Part of poll `{self.id}`. Split due to reaction count limit",
                                  colour=self.creator.colour, timestamp=datetime.utcnow())

            embed.add_field(name=f"Options continued", value="\n".join(lines[i:limit]), inline=False)
            embeds.append(embed)

        messages = []
        for embed in embeds:
            if not self.running: return messages
            message = await self.ctx.send(embed=embed)
            messages.append(message)

        print("Sent poll")
        return messages

    def create_tasks(self, messages):
        # Create async tasks for simultaneous processing so can support multiple messages
        self.tasks = [asyncio.ensure_future(self.message_count(msg, i * 20, i * 20 + 20)) for i, msg in enumerate(messages)]
        print("Created tasks")

    # Counter per message
    async def message_count(self, msg, min_ind, max_ind):
        if max_ind > len(self.options): max_ind = len(self.options)
        try:
            def check(reaction, user):  # Verification function. Checks react is on correct message and symbol
                em = str(reaction.emoji)
                return reaction.message.id == msg.id and (not user.bot) and \
                       (em == clear_symbol or min_ind <= indexes[em] < max_ind)

            while True:
                try:  # Continually check for reacts on message, if found call count_vote on it
                    reaction, user = await self.bot.wait_for("reaction_add", check=check)
                    await msg.remove_reaction(reaction, user)

                    # If reaction is clear symbol, remove user's reacts
                    em = str(reaction.emoji)
                    if em == clear_symbol:
                        ind = self.clear_votes(user)
                        result = "clear votes"

                    elif em in indexes:
                        ind = indexes[em]
                        result = self.count_vote(ind, user)
                    else: continue
                    await self.give_feedback(result, user, ind)

                except asyncio.TimeoutError:
                    pass
        except asyncio.exceptions.CancelledError:  # Propagate different error as CancelledError is caught in gather
            raise CancelException

    async def add_reactions(self, messages):
        # Add reactions, discord has max of 20 per message
        for i0 in range(len(messages)):
            if not self.running: return
            m = messages[i0]
            limit = min(i0 * 20 + 20, len(self.options))
            for i in range(i0 * 20, limit):
                await m.add_reaction(symbols[i])

        msg = messages[len(self.options) // 20]
        await msg.add_reaction(clear_symbol)

        print("Added reactions")

    async def post_results(self):
        print("Generating results")
        fields = self.make_results()

        split_fields = []
        for field in fields:
            title = field[0]
            lines = field[1]
            inline = field[2]

            split_fields.append((title, "\n".join(lines if len(lines) < 20 else lines[:20]), inline))
            for i in range(20, len(lines), 20):
                limit = min(i + 20, len(lines))
                split_fields.append((title + f" part {i//20+1}/{(len(lines)+19) // 20}", "\n".join(lines[i:limit]), inline))

        embed = discord.Embed(title="Results: " + self.question, colour=self.creator.colour, timestamp=datetime.utcnow())
        msg_length = 0
        part = 1
        for n, v, i in split_fields:
            msg_length += len(v)
            if msg_length > 4000:
                await self.ctx.send(embed=embed)
                part += 1
                embed = discord.Embed(title=f"Results part{part}: " + self.question, colour=self.creator.colour, timestamp=datetime.utcnow())

            embed.add_field(name=n, value=v, inline=i)

        await self.ctx.send(embed=embed)



    def make_votes(self):
        return self.Votes(len(self.options))


    def count_vote(self, ind, user):
        users_votes = self.votes.user_votes[user]
        if self.limit and len(users_votes) >= self.limit:
            return "over limit"

        voters = self.votes.votes[ind]

        if user not in voters:
            voters.add(user)
            self.votes.counts[ind] += 1
            users_votes.append(ind)

            print(ind, self.votes.counts)
            return "added vote"
        else:
            voters.remove(user)
            self.votes.counts[ind] -= 1
            users_votes.remove(ind)

            print(ind, self.votes.counts)
            return "removed vote"


    def make_results(self):
        return [self.top_n_results(5),
                self.list_results(range(len(self.options)))]


    def end(self):
        self.running = False
        for t in self.tasks:  # Cancel all tasks
            t.cancel()
        running_votes.pop(self.id)


    async def give_feedback(self, result, user, index):
        await user.create_dm()
        print(f"Sending DM for {result} to {user}")

        if result == "added vote": await user.dm_channel.send(f"Poll {self.id}: Counted your vote for {symbols[index]} **{self.options[index]}**")
        elif result == "removed vote": await user.dm_channel.send(f"Poll {self.id}: Removed your vote for {symbols[index]} **{self.options[index]}**")

        elif result == "over limit":
            await user.dm_channel.send(f"Poll {self.id}: Your vote for **{self.options[index]}** was **not counted**. You have voted for the **maximum of {self.limit}** choices. \n"
                                       f"\t\t**Remove a vote** before voting again: \n\t\tYour current choices are:\n\t\t\t" +
                                       '\n\t\t\t'.join(f"{symbols[i]} **{self.options[i]}**" for i in self.votes.user_votes[user])
                                       )
        elif result == "clear votes": await user.dm_channel.send(f"Poll {self.id}: Your votes have been cleared for:\n\t\t" +
                                                                 '\n\t\t'.join(f"{symbols[i]} **{self.options[i]}**" for i in index))


    def clear_votes(self, user):
        for index in self.votes.user_votes[user]:
            self.votes.counts[index] -= 1
            self.votes.votes[index].remove(user)
        return self.votes.user_votes.pop(user)

    @staticmethod
    # Generates a poll_id as a random number that is not present in the current list
    def pick_id():
        id = 0
        while id in running_votes:
            id = random.randint(0, 10000000)
        return id


    # Constructs the output embed field for a set of votes ordered by order
    def list_results(self, order, title="Results", votes = None):
        if votes is None: votes = self.votes.counts

        start_msg = ""
        if len(self.options) > 20:   # If long, only display non-zero results
            order = [p for p in order if votes[p] > 0]
            start_msg = "As a large number of results, omitting options with zero votes\n"
            if len(order) == 0: return title, start_msg + "All options received 0 votes.", False

        return title, [start_msg] + [f"{symbols[i]} **{self.options[i]}**: **{votes[i]}** votes" for i in order], False


    # Gets the top n results of options by votes
    def top_n_results(self, n):
        top = list(range(len(self.options)))
        top.sort(key=lambda x: -self.votes.counts[x])

        n = min(n, len(self.options))
        return self.list_results(top[:n], f"Top {n}")

    class Votes:
        def __init__(self, n):
            self.counts = [0 for _ in range(n)]
            self.votes = [set() for _ in range(n)]
            self.user_votes = defaultdict(lambda: list())  # set()


class STVPoll(Vote):
    def __init__(self, ctx, bot, args):
        super().__init__(ctx, bot, args, f"React to cast a vote for an option, **in order of your preference**. You may vote for **{'multiple' if args.limit == 0 else args.limit}**. "
                                         f"Reacts will be removed once counted. End the vote with `!close {self.id}`.")
        self.winners = args.winners

    def make_results(self):
        counts = Counter()
        first_pref_votes = Counter()

        for uv in self.votes.user_votes.values():
            print(uv)
            counts[tuple(uv)] += 1
            first_pref_votes[uv[0]] += 1

        indexes = list(range(len(self.options)))
        print("Votes parcelled ", counts, first_pref_votes)
        vote = stv.STV(indexes.copy(), counts, self.winners)
        winners = vote.run()
        print("STV Run, winners are", winners)

        first_prefs = indexes.copy()
        first_prefs.sort(key=lambda x: -first_pref_votes[x])

        return [("STV Winners", [f"{symbols[i]} **{self.options[i]}**" for i in winners] if winners else ["No winners."], False),
                self.list_results(first_prefs, "First Preference Votes", votes=first_pref_votes)]


    def count_vote(self, ind, user):
        users_votes = self.votes.user_votes[user]
        if self.limit and len(users_votes) >= self.limit:
            return "over limit"

        voters = self.votes.votes[ind]

        if user not in voters:
            voters.add(user)
            self.votes.counts[ind] += 1
            users_votes.append(ind)

            print(ind, self.votes.counts)
            return "added vote"
        else:
            return "already counted"


    async def give_feedback(self, result, user, index):
        await user.create_dm()
        print(f"Sending DM for {result} to {user}")

        if result == "added vote": await user.dm_channel.send(f"Poll {self.id}: Counted your vote for {symbols[index]} **{self.options[index]}** at position {self.votes.user_votes[user].index(index)+1}")
        elif result == "removed vote": await user.dm_channel.send(f"Poll {self.id}: Removed your vote for {symbols[index]} **{self.options[index]}**")

        elif result == "over limit":
            await user.dm_channel.send(f"Poll {self.id}: Your vote for **{self.options[index]}** was **not counted**. You have voted for the **maximum of {self.limit}** choices. \n"
                                       f"\t\t**Remove a vote** before voting again: \n\t\tYour current choices are:\n\t\t\t" +
                                       '\n\t\t\t'.join(f"{symbols[i]} **{self.options[i]}**" for i in self.votes.user_votes[user])
                                       )
        elif result == "clear votes": await user.dm_channel.send(f"Poll {self.id}: Your votes have been cleared for:\n\t\t" +
                                    '\n\t\t'.join(f"{symbols[i]} **{self.options[i]}**" for i in index))
        elif result == "already counted": await user.dm_channel.send(f"Poll {self.id}: You have **already voted** for {self.options[index]} option as preference #{self.votes.user_votes[user].index(index)+1}. To change your ordering, **clear votes** and enter your updated order.\n"
                                                                     f"your current preferences are:\n\t\t" +
                                    '\n\t\t'.join(f"{i+1}: {symbols[c]} **{self.options[c]}**" for i, c in enumerate(self.votes.user_votes[user])))


class CancelException(Exception):
    pass
