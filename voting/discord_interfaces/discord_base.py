from typing import Dict, Iterable, List, NamedTuple, Tuple, Union

import discord
from discord import AllowedMentions, ButtonStyle, InteractionMessage
from discord.ext.commands import Context
from discord.ui import Button, View
from sqlalchemy.exc import SQLAlchemyError

from models import db_session
from models.votes import DiscordVote, DiscordVoteChoice, DiscordVoteMessage, VoteType
from voting.vote_types.base_vote import base_vote

DENSE_ARRANGE = True
Chunk = NamedTuple("Chunk", [("start", int), ("end", int), ("choices", List[str])])

# Records last ephemeral message to each user, so can edit for future votes
class VoteButton(Button):
    def __init__(self, interface, dvc: DiscordVoteChoice, msg_title):
        super().__init__(label=dvc.choice.choice)  # , emoji=dvc.emoji)
        self.dvc = dvc
        self.vote = dvc.choice.vote
        self.msg_title = msg_title
        self.interface = interface

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        msg = self.interface.vote_type.vote_for(self.vote, user, self.dvc.choice)
        user_votes = self.interface.vote_type.get_votes_for_user(self.vote, user)
        await self.interface.send_choice_feedback(
            interaction, (user.id, self.vote.id), msg, self.msg_title, user_votes
        )


class CloseButton(Button):
    def __init__(self, interface, vote):
        super().__init__(label="End", emoji="✖️", style=ButtonStyle.danger)
        self.interface = interface
        self.vote = vote

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if user.id == self.vote.owner_id:
            await interaction.message.edit(view=None)
            await self.interface.end_vote(interaction, self.vote)
            self.interface.vote_type.end(self.vote)


class MyVotesButton(Button):
    def __init__(self, interface, vote, msg_title):
        super().__init__(label="My Votes", emoji="🗳️", style=ButtonStyle.green)
        self.vote = vote
        self.msg_title = msg_title
        self.interface = interface

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        votes = self.interface.vote_type.get_votes_for_user(self.vote, user)
        await self.interface.send_choice_feedback(
            interaction,
            (user.id, self.vote.id),
            "_ _",
            self.msg_title,
            votes,
            create_new_msg=True,
        )


class DiscordBase:
    def __init__(self, bot, vote_type=base_vote, btn_class=VoteButton):
        self.bot = bot
        self.vote_type = vote_type
        self.BtnClass = btn_class
        self.users_last_vote_update_message: Dict[
            Tuple[int, int], InteractionMessage
        ] = {}

    def recreate_view(self, vid, msg, dvm):
        view = View()
        vote = dvm.discord_vote.vote
        msg_title = self.get_title(vote.title, dvm.part)
        s, e = dvm.choices_start_index, dvm.choices_start_index + dvm.numb_choices
        msg_choices = (
            db_session.query(DiscordVoteChoice)
            .filter(DiscordVoteChoice.vote_id == vid)
            .filter(s <= DiscordVoteChoice.choice_index)
            .filter(DiscordVoteChoice.choice_index < e)
            .all()
        )
        for dvc in msg_choices:
            view.add_item(self.BtnClass(self, dvc, msg_title))

        if s == 0:
            view.add_item(CloseButton(self, vote))
            view.add_item(MyVotesButton(self, vote, msg_title))
        return view

    async def create_vote(
        self, ctx: Context, args: List[str], vote_limit=None, seats=None
    ):
        title, choices = self.parse_choices(args)

        try:
            # Create DB entry for vote
            user_id = ctx.author.id
            vote_obj, choices_obj = self.vote_type.create_vote(
                title, user_id, choices, VoteType.basic, vote_limit, seats
            )
            new_dc_vote = DiscordVote(vote=vote_obj)
            db_session.add(new_dc_vote)

            # Post messages
            msg_index = 0
            for chunk in self.chunk_choices(choices):
                msg_title = self.get_title(title, msg_index)
                # Send msg
                # embed = self.create_embed(chunk.choices, title)
                msg = await ctx.send(
                    content=msg_title, allowed_mentions=AllowedMentions.none()
                )

                # Add msg to DB
                start_ind, end_ind = chunk.start, chunk.end
                new_dc_msg = DiscordVoteMessage(
                    message_id=msg.id,
                    channel_id=msg.channel.id,
                    discord_vote=new_dc_vote,
                    choices_start_index=start_ind,
                    numb_choices=end_ind - start_ind,
                    part=msg_index,
                )
                db_session.add(new_dc_msg)
                msg_index += 1

                # Add choices to DB and add buttons
                view = View(timeout=None)
                for db_ch in choices_obj[start_ind:end_ind]:
                    new_dc_choice = DiscordVoteChoice(
                        choice=db_ch, emoji="", msg=new_dc_msg
                    )
                    db_session.add(new_dc_choice)

                    view.add_item(self.BtnClass(self, new_dc_choice, msg_title))

                if start_ind == 0:
                    view.add_item(CloseButton(self, vote_obj))
                    view.add_item(MyVotesButton(self, vote_obj, msg_title))
                await msg.edit(view=view)

            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            await ctx.send("Error creating vote")
            raise

    def get_title(self, title, msg_index):
        if msg_index == 0:
            return f"**Basic Vote: {title}**"
        else:
            return f"**Basic Vote: {title} pt. {msg_index+1}**"

    def get_description(self):
        return "Votes: Visible"

    def parse_choices(self, args: List[str]) -> Tuple[str, List[str]]:
        """Parse title and choices out of args"""
        if len(args) > 256:
            raise Exception(f"More than 256 choices given")
        if len(args) == 0:
            raise Exception(f"No choices given")

        # Truncate each choice to 256 chars
        for i, c in enumerate(args):
            if len(c) > 250:
                args[i] = c[:250] + "..."

        # Title is first argument
        title = args[0]
        choices = args[1:]

        # Pair choices with emojis -- thumbs up/down if single option given
        if len(choices) <= 1:
            c = choices[0] if choices else ""
            return title, [f"👍 {c}", f"👎 {c}"]
        else:
            return title, choices

    def chunk_choices(
        self, choices: List[str], per_msg=20, len_per_msg=5900
    ) -> Iterable[Chunk]:
        """Splits options such that they'll fit onto a message. Each msg can have 20 reacts and each embed can have max 6000 chars for the whole thing"""
        chunk, msg_len = [], 0
        for i, choice in enumerate(choices):
            line_len = len(choice) + 4
            if len(chunk) + 1 > per_msg or msg_len + line_len > len_per_msg:
                yield Chunk(i - len(chunk), i, chunk)
                chunk, msg_len = [], 0
            chunk.append(choice)
            msg_len += line_len
        if chunk:
            yield Chunk(len(choices) - len(chunk), len(choices), chunk)

    def create_embed(
        self, lines: Union[List[str], List[Tuple[str, str]]], title: str = None
    ):
        """Construct embed from list of choices"""
        if not type(lines) is tuple:
            lines = [(l, "_ _") for l in lines]
        embed = discord.Embed(title=self.get_description() if title is None else title)
        for n, v in lines:
            if len(n) > 250:
                n = n[:250]
            embed.add_field(
                name=n, value=v, inline=(DENSE_ARRANGE and len(n) + len(v) < 25)
            )
        return embed

    async def send_choice_feedback(
        self,
        interaction: discord.Interaction,
        key,
        msg,
        msg_title,
        user_votes,
        create_new_msg=False,
    ):
        ch = [vc.choice for vc in user_votes]
        embed = self.create_embed(ch, "Your Votes")

        # Check if existing feedback message and attempt to send to it
        if not create_new_msg and (
            old_msg := self.users_last_vote_update_message.get(key)
        ):
            try:
                await old_msg.edit(content=msg, embed=embed)
                # Hack to give interaction a response without changing anything
                await interaction.response.edit_message(content=f"**{msg_title}**")
                return
            except (discord.errors.NotFound, discord.errors.HTTPException):
                pass
        # If no existing message, send it and update record for user
        await interaction.response.send_message(msg, embed=embed, ephemeral=True)
        new_msg = await interaction.original_response()
        self.users_last_vote_update_message[key] = new_msg

    async def end_vote(self, interaction: discord.Interaction, vote_id):
        votes = self.vote_type.get_votes_for(vote_id)

        options = []
        last_pos, last_count = 1, -1
        for i, (v, c) in enumerate(votes):
            pos = i + 1
            if c == last_count:
                pos = f"={last_pos}"
                options[-1] = (pos, options[-1][1])
            else:
                last_pos, last_count = pos, c
            options.append((pos, f"{v.choice}**: {c} vote{'s' if c != 1 else ''}"))

        embed = discord.Embed(title="Vote Results:")
        embed.add_field(
            name="Results",
            value="\n".join(f"**{o[0]}) {o[1]}" for o in options),
            inline=False,
        )

        await interaction.response.edit_message(embed=embed)
