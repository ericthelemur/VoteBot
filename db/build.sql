CREATE TABLE IF NOT EXISTS Prefix (
    GuildID BIGINT PRIMARY KEY,
    Prefix TEXT DEFAULT '+'
);

CREATE TABLE IF NOT EXISTS Votes (
    VoteID BIGSERIAL PRIMARY KEY,
    CreatorID BIGINT,
    Question TEXT DEFAULT 'Poll',
    VoteLimit INTEGER DEFAULT 0,
    GuildID BIGINT NOT NULL,
    ChannelID BIGINT NOT NULL,
    PollStage INTEGER NOT NULL,
    Type INTEGER NOT NULL,
    NumWinners INTEGER DEFAULT 1,
    CreationDate TIMESTAMP DEFAULT NOW()
);
-- Stage: 0 = Created, 1 = Posted, 2 = Reactions added - running, -1 = Finished
-- Type: 0 = Quick Poll, 1 = Standard Poll, 2 = STV Poll

CREATE TABLE IF NOT EXISTS Options (
    VoteID BIGINT,
    OptionNumb INTEGER,
    Prompt TEXT NOT NULL,
    PRIMARY KEY (VoteID, OptionNumb),
    FOREIGN KEY (VoteID) REFERENCES Votes(VoteID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS VoteMessages (
    VoteID BIGINT,
    MessageID BIGINT,
    Part INTEGER NOT NULL,
    PRIMARY KEY (MessageID),
    FOREIGN KEY (VoteID) REFERENCES Votes(VoteID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UserVote (
    VoteID BIGINT,
    UserID BIGINT,
    Choice INTEGER NOT NULL,
    Preference INTEGER NOT NULL,
    PRIMARY KEY (VoteID, UserID, Choice),
    FOREIGN KEY (VoteID) REFERENCES Votes(VoteID) ON DELETE CASCADE
);