import discord

from db import db


@db.with_commit
def addVote(creator: discord.User, question: str, options: list[str], limit: int, guild: discord.Guild, channel: discord.TextChannel, stage: int = 0, type: int = 1) -> int:
    db.execute("INSERT INTO Votes (CreatorID, Question, ResponseLimit, GuildID, ChannelID, PollStage, Type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     creator.id, question, limit, guild.id, channel.id, stage, type)

    vid = db.cur.lastrowid
    db.multiexec("INSERT INTO Options (VoteID, OptionNumb, Prompt) VALUES (?, ?, ?)", ((vid, i, p) for i, p in enumerate(options)))
    return vid


@db.with_commit
def removeVote(vid: int):
    db.execute("DELETE FROM Votes WHERE VoteID = ?", vid)
    # Should cascade to others


@db.with_commit
def addMessage(vid: int, mid: int, part: int):
    print("Add msg", vid, mid, part)
    db.execute("INSERT INTO Messages (VoteID, MessageID, Part) VALUES (?, ?, ?)", vid, mid, part)


@db.with_commit
def addUserVote(vid: int, uid: int, choice: int, pref: int):
    db.execute("INSERT INTO UserVote (VoteID, UserID, Choice, Preference) VALUES (?, ?, ?, ?)", vid, uid, choice, pref)


@db.with_commit
def removeUserVote(vid: int, uid: int, choice: int = None):
    if choice is None: return db.execute("DELETE FROM UserVote WHERE UserID = ? AND VoteID = ? RETURNING Choice", uid, vid)
    else: db.execute("DELETE FROM UserVote WHERE UserID = ? AND VoteID = ? AND Choice = ?", uid, vid, choice)


def toggleUserVote(vid: int, uid: int, choice: int, pref: int):
    if getUserPref(vid, uid, choice) == -1:
        addUserVote(vid, uid, choice, pref)
        return True
    else:
        removeUserVote(vid, uid, choice)
        return False


def getUserVotes(vid: int, uid: int = None):
    if uid is None: return db.execute("SELECT UserID, Choice, Preference FROM UserVote WHERE VoteID = ? ORDER BY UserID, Choice, Preference", vid).fetchall()
    else: return db.execute("SELECT Choice, Preference FROM UserVote WHERE VoteID = ? AND UserID = ? ORDER BY Choice, Preference", vid, uid).fetchall()


def getUserVoteCount(vid: int, choice: int = None, uid: int = None):
    if choice is None:
        if uid is None:
            vs = db.execute("SELECT O.OptionNumb, COALESCE(T.Count, 0) FROM Options O LEFT JOIN "
                                          "(SELECT O.OptionNumb AS Numb, COUNT(*) AS Count "
                                          "FROM Options O JOIN UserVote UV ON (UV.VoteID = O.VoteID AND UV.Choice = O.OptionNumb) "
                                          "WHERE O.VoteID = ? GROUP BY O.OptionNumb ORDER BY COUNT(*) DESC "
                                        ") T ON O.OptionNumb = T.Numb WHERE O.VoteID = ?", vid, vid).fetchall()
            print(vs)
        else: vs = db.execute("SELECT COUNT(*) FROM UserVote WHERE VoteID = ? AND UserID = ?", vid, uid).fetchall()
    else:
        if uid is None: vs = db.execute("SELECT COUNT(*) FROM UserVote WHERE VoteID = ? AND Choice = ?", vid, choice).fetchall()
        else: vs = db.execute("SELECT COUNT(*) FROM UserVote WHERE VoteID = ? AND UserID = ? AND Choice = ?", vid, uid, choice).fetchall() # Of questionable usefulness, but present for completeness

    return vs


def getUserNextPref(vid: int, uid: int):
    vs = db.execute("SELECT COALESCE(MAX(Preference), 0) FROM UserVote WHERE VoteID = ? AND UserID = ?", vid, uid).fetchall()
    return 1 + extract1Val(vs)


def getUserPref(vid: int, uid: int, choice: int):
    vs = db.execute("SELECT COALESCE(Preference, -1) FROM UserVote WHERE VoteID = ? AND UserID = ? AND Choice = ?", vid, uid, choice).fetchall()
    return extract1Val(vs)


def allowedEnd(vid: int, uid: int):
    vs = db.execute("SELECT EXISTS(SELECT 1 FROM Votes WHERE VoteID = ? AND CreatorID = ?)", vid, uid).fetchall()
    return extract1Val(vs, False)


@db.with_commit
def updateStage(vid: int, stage: int):
    db.execute("UPDATE Values SET PollStage = ? WHERE VoteID = ?", stage, vid)


def extract1Row(vals, default=-1):
    if len(vals) > 0: return vals[0]
    else: return default


def extract1Val(vals, default=-1):
    r = extract1Row(vals, default)
    if r == default: return default
    return r[0]

