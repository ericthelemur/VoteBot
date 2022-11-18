# Apollo [![Build status](https://github.com/UWCS/apollo/actions/workflows/tests.yaml/badge.svg?branch=master)](https://github.com/UWCS/apollo/actions/workflows/tests.yaml)

Apollo is a [Discord](https://discordapp.com/) bot for the [University of Warwick Computing Society](https://uwcs.co.uk).
It is designed to augment our Discord server with a few of the user services available on our website.

Apollo is based loosely on the development of [artemis](https://github.com/rhiannonmichelmore/artemis), another Discord bot produced by a member of UWCS.

### Installation

#### Dependencies

Two type of dependency files are included with this project.
The first, `requirements.txt`, only includes top-level dependencies.

The second, `requirements-platform.lock`, contains a pinned list of all dependencies specific to a platform.

If installing the top-level dependencies does not work, try installing the pinned dependencies.

#### Environment Setup

1. Create a new virtual environment `python -m venv .venv`.
2. Activate the virtual environment
   - On Linux and macOS: `source .venv/bin/activate`.
   - On Windows: `.\.venv\Scripts\activate`
3. Check that the virtual environment has been activated.
   - On Linux and macOS: `which python`  
     Expected output: `.../.venv/bin/python`.
   - On Windows: `where python` (**NB** on PowerShell use `where.exe` or `Get-Command` instead of `where`)  
     Expected output: `...\.venv\Scripts\python.exe`.
4. Install dependencies.  
   Now that we've activated the environment, `pip` will install packages locally.
   - Installing top-level dependencies via `pip install -r requirements.txt` should work.
   - If it doesn't, you may need to install the pinned requirements via `pip install -r requirements.lock`
5. Copy `config.example.yaml` to `config.yaml` and configure the fields.
6. Copy `alembic.example.ini` to `alembic.ini`.
7. Set up the database by running migrations with `alembic upgrade head`.
   - The default database location is `postgresql://apollo:apollo@localhost/apollo` (in both `config.example.yaml` and `alembic.example.ini`).
     This requires PostgreSQL to be installed, with a database called `apollo` and a user with name and password `apollo` with access to it.
     For testing purposes, you may wish to change it to a locally stored file such as `sqlite:///local.sqlite3`.
8. On the [Discord developer portal](https://discord.com/developers/), make sure that your bot has the required intents.
   - Currently, only the Members intent is necessary.

#### Running Apollo

Run `apollo.py` - either with `python apollo.py` or just by executing the file.

### Contributor Notes

* When writing anything that needs to reply to a specific username, please do `from utils import get_name_string` and get the display string using this function, with the discord `Message` object as the argument (e.g. `display_name = get_name_string(ctx.message)`).
  This will return either a discord username, formatted correctly, or an irc nickname depending on the source of the message.
  Finally, this can be used as normal in a format string e.g. `await ctx.send(f'Sorry {display_name}, that won't work.')`.

* When writing a new command, please read in the rest of the message using `*args: clean_content` (see `cogs/commands/flip.py` as an example), and if you need it as one large string, use `" ".join(args)`.
  This is instead of reading the whole message content, which will likely break the irc bridging (unless you know what you're doing).

* This project uses the Black Python formatter.
  Before submitting your code for a PR, run `black .` on the root directory of this project to bring all of your up to spec for the code style guide.
  
* For testing CI locally, use [act-cli](https://github.com/nektos/act).

* The current production database engine is PostgreSQL.
  You may wish to use another database engine such as MySQL or SQLite for local testing.
  
#### Testing subsections

You may want to work on a subsection of the bot without the surrounding functionality. This may be useful if you want to add a basic command but don't want the hassle of installing and working around the database requirements. You can disable parts of the bot from being loaded in at runtime by disabling their cogs.

[Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html) are a method of categorising parts of your bot with discord.py. If you are to contribute to the project, some understanding of cogs and discord.py in general would be advisable, but you can see the implementation of pre-existing commands for a basic idea of how they work.

Cogs are loaded in [apollo.py](apollo.py):

```py
# The command extensions to be loaded by the bot
EXTENSIONS = [
    "cogs.commands.admin",
    "cogs.commands.blacklist",
    "cogs.commands.date",
    "cogs.commands.flip",
    "cogs.commands.karma",
    "cogs.commands.misc",
    # ...and so on
]
```

You can simply comment out any category of commands you don't want the bot to load to avoid supporting their requirements:

```py
# The command extensions to be loaded by the bot
EXTENSIONS = [
    "cogs.commands.admin",
    #    "cogs.commands.blacklist", # <- requires database
    "cogs.commands.date",
    "cogs.commands.flip",
    #    "cogs.commands.karma", # <- requires database
    "cogs.commands.misc",
    # ...and so on
]
```

Make sure not to commit these comments when you pull request.

### License

This project is distributed under the MIT license.

The MIT License (MIT)
=====================

Copyright © 2022 Apollo Contributors

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the “Software”), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
