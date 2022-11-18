import asyncio
import json
from datetime import date, datetime, time, timedelta
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import discord
import requests
from discord.ext import commands
from discord.ext.commands import Bot, Context

room_resource_root = Path() / "resources" / "rooms"
# Same for all requests from campus map, so hardcode here as well
map_api_token = "Token 3a08c5091e5e477faa6ea90e4ae3e6c3"


def req_or_none(url, **kwargs):
    r = requests.get(url, **kwargs)
    if not r.ok:
        return None
    return r.json()


def req_img(url):
    r = requests.get(url)
    bytes = BytesIO(r.content)
    return bytes


def read_json_file(filename):
    # Read room name to timetable url mapping
    with open(str(filename)) as f:
        return json.load(f)


class RoomSearch(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.full_emojis = ("1️⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟")

        root = room_resource_root
        self.central_rooms = read_json_file(root / "central-room-data.json")
        self.custom_room_names = read_json_file(root / "room-mapname.json")
        self.timetable_room_mapping = read_json_file(root / "room_to_surl.json")
        self.last_week_check = None
        self.year = None
        self.week = None

    @commands.hybrid_command()
    async def roompr(self, ctx: Context):
        await ctx.reply(
            "This bot uses the Campus Map's API (<https://campus.warwick.ac.uk/>)."
            "If a name is wrong/missing on there, either ask exec to add it, "
            "or create a PR to add an alias in `resources/rooms/room-mapname.json`"
        )

    @commands.hybrid_command()
    async def room(self, ctx: Context, *, name: str):
        """Warwick Room Search

        Finds a room on the various Warwick systems.
        """
        rooms = self.get_room_infos(name)
        if not rooms:
            return await ctx.reply(
                "Room does not exist. Try a more general search, "
                "or suggest a room alias (more info with `!roompr`)"
            )

        if len(rooms) > 1:
            room = await self.choose_room(ctx, rooms)
            if room is None:
                return
        else:
            room = rooms[0]  # Only one in rooms

        # Room info
        embed = discord.Embed(
            title=f"Room Search: {room.get('value')}",
            description=f"Building: **{room.get('building')} {room.get('floor')}**",
        )
        # Campus Map
        embed.add_field(
            name="Campus Map:",
            value=f"**[{room.get('value')}](https://campus.warwick.ac.uk/?cmsid={room.get('id')})**",
            inline=True,
        )

        # Room info (for centrally timetabled rooms)
        if url := self.is_central(room.get("value")):
            embed.add_field(
                name="Room Info:",
                value=f"**[{room.get('value')}](https://warwick.ac.uk/services/its/servicessupport/av/lecturerooms/roominformation/{url})**",
                inline=True,
            )

        # Timetable
        if tt_room_id := self.timetable_room_mapping.get(room.get("value")):
            self.get_week()
            if self.year:
                this_year = self.year.replace("/", "")
                if self.week < 52:
                    next_week_year = this_year
                    next_week = self.week + 1
                else:
                    year_int = int(this_year[:2])
                    next_week_year = f"{year_int+1}{year_int+2}"
                    next_week = 1
                embed.add_field(
                    name="Timetable:",
                    value=f"**[This Week](https://timetablingmanagement.warwick.ac.uk/SWS{this_year}/roomtimetable.asp?id={quote(tt_room_id)}&week={self.week})**\n"
                    f"[Next Week](https://timetablingmanagement.warwick.ac.uk/SWS{next_week_year}/roomtimetable.asp?id={quote(tt_room_id)}&week={next_week})\n",
                    inline=True,
                )

        # embed.set_image(url=f"https://search.warwick.ac.uk/api/map-thumbnail/{room.get('w2gid')}")
        # Slows command down quite a lot, but Discord can't take images without extensions
        img = discord.File(
            req_img(
                f"https://search.warwick.ac.uk/api/map-thumbnail/{room.get('w2gid')}"
            ),
            filename="map.png",
        )
        embed.set_image(url="attachment://map.png")
        embed.set_footer(
            text="Missing a room? Add it with a PR or ask exec to add an alias. !roompr for more"
        )
        await ctx.reply(embed=embed, file=img)

    async def choose_room(self, ctx, rooms):
        # Confirms room choice, esp. important with autocomplete api
        # Create and send message
        emojis = self.full_emojis[: len(rooms)]
        header = "Multiple rooms exist with that name. Which do you want?:"
        rooms_text = "".join(
            f"\n\t{e} {r.get('value')} in **{r.get('building')}** {r.get('floor')}"
            for r, e in zip(rooms, emojis)
        )
        conf_message = await ctx.send(header + rooms_text)

        # Add reacts to choice msg
        async def add_reacts():
            try:
                for e in emojis:
                    await conf_message.add_reaction(e)
            except discord.NotFound:
                pass

        # Check for user react on msg
        async def check_reacts():
            try:
                check = (
                    lambda r, u: r.message.id == conf_message.id
                    and u == ctx.message.author
                    and str(r.emoji) in emojis
                )
                react_emoji, _ = await ctx.bot.wait_for(
                    "reaction_add", check=check, timeout=30
                )
                return react_emoji
            except TimeoutError:
                return None
            finally:
                await conf_message.delete()

        # Add and check in parallel, so don't miss quick react
        _, react_emoji = await asyncio.gather(add_reacts(), check_reacts())

        # Get choice
        ind = emojis.index(str(react_emoji))
        return rooms[ind]

    def get_room_infos(self, room):
        stripped = room.replace(".", "").replace(" ", "").lower()
        if new := self.custom_room_names.get(stripped):
            room = new
        # Check Map Autocomplete API
        map_req = req_or_none(
            f"https://campus-cms.warwick.ac.uk//api/v1/projects/1/autocomplete.json?term={room}",
            headers={"Authorization": map_api_token},
        )
        if map_req is None:
            return []
        return self.remove_duplicate_rooms(map_req)

    def remove_duplicate_rooms(self, rooms):
        # Map has duplicate entries for MSB for some reason
        rooms = self.remove_duplicate_building(
            rooms, "Mathematical Sciences", "Mathematical Sciences Building"
        )
        return rooms

    def remove_duplicate_building(self, rooms, orig, copy):
        orig_rooms = [r for r in rooms if r.get("building") == orig]
        fake_rooms = [r for r in rooms if r.get("building") == copy]
        for orig_room in orig_rooms:
            fake_room = next(
                (r for r in fake_rooms if orig_room.get("value") == r.get("value")),
                None,
            )
            if fake_room:
                rooms.remove(fake_room)
        return rooms

    def get_week(self):
        # Definitely don't need to check each request
        # Only check if last request was before today
        today = datetime.combine(date.today(), time.min)

        if self.last_week_check is None or self.last_week_check < today:
            self.last_week_check = datetime.now()
            weeks_json = req_or_none(
                "https://tabula.warwick.ac.uk/api/v1/termdates/weeks"
            ).get("weeks")

            for week in weeks_json:
                start = datetime.strptime(week.get("start"), "%Y-%m-%d").date()
                end = datetime.strptime(week.get("end"), "%Y-%m-%d").date()
                current = (datetime.now() + timedelta(days=3)).date()
                if start < current <= end:
                    self.year = week.get("academicYear")
                    self.week = week.get("weekNumber")
                    return self.year, self.week
            return None, None
        return self.year, self.week

    def is_central(self, room_name):
        # Checks if room is centrally timetabled from central-room-data.json (from Tabula)
        for building in self.central_rooms:
            for r in building.get("rooms"):
                if r.get("name") == room_name:
                    return r.get("url")
        return None


async def setup(bot: Bot):
    await bot.add_cog(RoomSearch(bot))
