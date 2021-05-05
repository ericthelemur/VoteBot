CREATE TABLE IF NOT EXISTS Prefix (
    GuildID INTEGER PRIMARY KEY,
    Prefix TEXT DEFAULT '+'
);

CREATE TABLE IF NOT EXISTS Votes (
    VoteID INTEGER PRIMARY KEY AUTOINCREMENT,
    CreatorID INTEGER,
    Question TEXT DEFAULT 'Poll',
    VoteLimit INTEGER DEFAULT 0,
    GuildID INTEGER NOT NULL,
    ChannelID INTEGER NOT NULL,
    PollStage INTEGER NOT NULL,
    Type INTEGER NOT NULL,
    NumWinners INTEGER DEFAULT 1
);
-- Stage: 0 = Created, 1 = Posted, 2 = Reactions added - running, -1 = Finished
-- Type: 0 = Quick Poll, 1 = Standard Poll, 2 = STV Poll

CREATE TABLE IF NOT EXISTS Options (
    VoteID INTEGER,
    OptionNumb INTEGER,
    Prompt TEXT NOT NULL,
    PRIMARY KEY (VoteID, OptionNumb),
    FOREIGN KEY (VoteID) REFERENCES Votes(VoteID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Messages (
    VoteID INTEGER,
    MessageID INTEGER,
    Part INTEGER NOT NULL,
    PRIMARY KEY (MessageID),
    FOREIGN KEY (VoteID) REFERENCES Votes(VoteID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UserVote (
    VoteID INTEGER,
    UserID INTEGER,
    Choice INTEGER NOT NULL,
    Preference INTEGER NOT NULL,
    PRIMARY KEY (VoteID, UserID, Choice),
    FOREIGN KEY (VoteID) REFERENCES Votes(VoteID) ON DELETE CASCADE
);