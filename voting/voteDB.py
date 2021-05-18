from pprint import pprint
from typing import Union

import discord

from db import db


def setPrefix(gid, prefix):
    db.execute("INSERT INTO Prefix (GuildID, Prefix) VALUES (%s, %s) ON CONFLICT (GuildID) DO UPDATE SET Prefix = EXCLUDED.Prefix;", gid, prefix)
    pprint(db.executeFAll("SELECT * FROM Prefix;"))


def getPrefix(gid: int):
    prefix = db.executeF1("SELECT COALESCE(Prefix, '+') FROM Prefix WHERE GuildID = %s;", gid)
    if not prefix: return "+"
    return prefix[0]

@db.with_commit
def addVote(creator: discord.User, question: str, options: list[str], limit: int, guild: discord.Guild, channel: discord.TextChannel, stage: int = 0, type: int = 1, num_win: int = 1) -> int:
    vid = db.executeF1("INSERT INTO Votes (CreatorID, Question, VoteLimit, GuildID, ChannelID, PollStage, Type, NumWinners) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING VoteID;",
               creator.id, question, limit, guild.id, channel.id, stage, type, num_win)[0]

    db.multiexec("INSERT INTO Options (VoteID, OptionNumb, Prompt) VALUES (%s, %s, %s);", ((vid, i, p) for i, p in enumerate(options)))
    return vid


@db.with_commit
def removeVote(vid: int):
    db.execute("DELETE FROM Votes WHERE VoteID = %s;", vid)
    # Should cascade to others


def getVote(vid: int):
    return db.executeF1("SELECT CreatorID, Question, GuildID, ChannelID, Type, NumWinners "
                      "FROM Votes WHERE VoteID = %s;", vid)


def getMsgVote(mid: int):
    return db.executeF1("SELECT M.VoteID, Part, Type, VoteLimit, PollStage "
                        "FROM VoteMessages M JOIN Votes V USING (VoteID) WHERE MessageID = %s;", mid)


@db.with_commit
def addMessage(vid: int, mid: int, part: int):
    db.execute("INSERT INTO VoteMessages (VoteID, MessageID, Part) VALUES (%s, %s, %s);", vid, mid, part)


def getMessages(vid: int = None):
    if vid: return db.executeFAll("SELECT GuildID, ChannelID, MessageID "
                              "FROM Votes JOIN VoteMessages USING (VoteID) "
                              "WHERE PollStage > -1 AND VoteID = %s;", vid)

    else: return db.executeFAll("SELECT VoteID, GuildID, ChannelID, MessageID "
                            "FROM Votes JOIN VoteMessages USING (VoteID) "
                            "WHERE PollStage >= 0;")


@db.with_commit
def addUserVote(vid: int, uid: int, choice: int, pref: int):
    db.execute("INSERT INTO UserVote (VoteID, UserID, Choice, Preference) VALUES (%s, %s, %s, %s);", vid, uid, choice, pref)


@db.with_commit
def removeUserVote(vid: int, uid: int, choice: int = None):
    if choice is None:
        sel = db.executeFAll("SELECT Choice FROM UserVote WHERE UserID = %s AND VoteID = %s;", uid, vid)
        db.execute("DELETE FROM UserVote WHERE UserID = %s AND VoteID = %s;", uid, vid)
        return [s[0] for s in sel]
    else: db.execute("DELETE FROM UserVote WHERE UserID = %s AND VoteID = %s AND Choice = %s;", uid, vid, choice)


def toggleUserVote(vid: int, uid: int, choice: int, pref: int):
    if getUserPref(vid, uid, choice) == -1:
        addUserVote(vid, uid, choice, pref)
        return True
    else:
        removeUserVote(vid, uid, choice)
        return False

def prefUserVote(vid: int, uid: int, choice: int, pref: int):
    if getUserPref(vid, uid, choice) == -1:
        addUserVote(vid, uid, choice, pref)
        return True
    else:
        return False

def getUserVotes(vid: int, uid: int = None):
    if uid is None: return db.executeFAll("SELECT UserID, Choice, Preference FROM UserVote WHERE VoteID = %s ORDER BY UserID, Choice, Preference;", vid)
    else: return db.executeFAll("SELECT Choice, Preference FROM UserVote WHERE VoteID = %s AND UserID = %s ORDER BY Choice, Preference;", vid, uid)


def getOptions(vid: int):
    return db.executeFAll("SELECT OptionNumb, Prompt FROM Options WHERE VoteID = %s ORDER BY OptionNumb;", vid)


def getUserVoteCount(vid: int, choice: int = None, uid: int = None) -> Union[int, list]:
    if choice is None:
        if uid is None:
            return db.executeFAll("SELECT O.OptionNumb, COALESCE(T.Count, 0) AS Count FROM Options O LEFT JOIN ("
                            "    SELECT O2.OptionNumb AS Numb, COUNT(*) AS Count "
                            "    FROM Options O2 JOIN UserVote UV ON (UV.VoteID = O2.VoteID AND UV.Choice = O2.OptionNumb) "
                            "    WHERE O2.VoteID = %s GROUP BY O2.OptionNumb"
                            ") T ON O.OptionNumb = T.Numb WHERE O.VoteID = %s ORDER BY Count DESC;", vid, vid)

        else: vs = db.executeF1("SELECT COUNT(*) FROM UserVote WHERE VoteID = %s AND UserID = %s;", vid, uid)
    else:
        if uid is None: vs = db.executeF1("SELECT COUNT(*) FROM UserVote WHERE VoteID = %s AND Choice = %s;", vid, choice)
        else: vs = db.executeF1("SELECT COUNT(*) FROM UserVote WHERE VoteID = %s AND UserID = %s AND Choice = %s;", vid, uid, choice) # Of questionable usefulness, but present for completeness

    if vs: return vs[0]
    else: return 0


def getVoterCount(vid: int):
    return db.executeF1("SELECT COUNT(DISTINCT UserID) FROM Votes V JOIN UserVote UV USING (VoteID) WHERE VoteID = %s", vid)[0]


def getUserNextPref(vid: int, uid: int):
    vs = db.executeFAll("SELECT COALESCE(MAX(Preference), -1) FROM UserVote WHERE VoteID = %s AND UserID = %s;", vid, uid)
    return 1 + extract1Val(vs)


def getUserPref(vid: int, uid: int, choice: int):
    vs = db.executeFAll("SELECT COALESCE(Preference, -1) FROM UserVote WHERE VoteID = %s AND UserID = %s AND Choice = %s;", vid, uid, choice)
    return extract1Val(vs)


def allowedEnd(vid: int, uid: int):
    vs = db.executeFAll("SELECT EXISTS(SELECT 1 FROM Votes WHERE VoteID = %s AND CreatorID = %s);", vid, uid)
    return extract1Val(vs, False)


@db.with_commit
def updateStage(vid: int, stage: int):
    db.execute("UPDATE Votes SET PollStage = %s WHERE VoteID = %s;", stage, vid)


def extract1Row(vals, default=-1):
    if len(vals) > 0: return vals[0]
    else: return default


def extract1Val(vals, default=-1):
    r = extract1Row(vals, default)
    if r == default: return default
    return r[0]

