from collections import Counter
import random

names = ["orange", "pear", "chocolate", "strawberries", "hamburgers"]

# STV implemented according to Scottish STV rules from https://www.opavote.com/methods/scottish-stv-rules
# Summarized in https://blog.opavote.com/2016/11/plain-english-explanation-of-scottish.html


class STV:
    def __init__(self, choices: list[int], preferences: Counter, winner_count: int):
        # self.choices = [c for c in choices]
        self.choices = choices
        self.preferences = preferences
        self.votes = self.calc_votes()
        self.total_votes = sum(self.votes.values())
        # self.choices = [c for c in choices if self.votes[c] > 0]

        self.winner_count = winner_count
        self.win_quota = (self.total_votes // (self.winner_count + 1)) + 1
        self.winners = []
        self.round_no = 0
        self.report = []
        self.tie_weights = Counter()  # Breaks ties based on number of votes in previous rounds
        self.round_weight = 1
        print(self.win_quota, self.votes)

    def calc_votes(self):
        votes = Counter()
        for pref in self.preferences:
            votes[pref[0]] += self.preferences[pref]
        print(votes)
        return votes

    def run(self):
        while len(self.winners) < self.winner_count:
            self.round_no += 1
            print("Running round", self.round_no)

            for c in self.choices:
                self.tie_weights[c] += self.votes[c] * self.round_weight
            print("Weights", self.round_weight, self.tie_weights)

            self.round()
            print(self.choices, self.votes, len(self.winners), self.winner_count)

            if self.round_no > 1000:
                print("Way too many rounds, ending...")
                break

            self.round_weight *= self.total_votes
        return self.winners

    def round(self):
        # If available choices <= winners remaining to allocate, declare all winners
        if len(self.choices) <= self.winner_count - len(self.winners):
            print(f"Only {len(self.choices)} choices remaining, and {self.winner_count - len(self.winners)} places")
            self.winners += self.choices
        else:
            over_quota = []
            # Declare winners as choices above threshold
            for choice in self.choices:
                if self.votes[choice] >= self.win_quota:
                    over_quota.append(choice)

            # Redistribute surplus winner votes
            if over_quota:
                # Reassign most voted choice first, others will be processed in following rounds
                choice = max(over_quota, key=lambda x: (self.votes[x], self.tie_weights[x], random.random()))   # Pick by votes, then previous round's votes, then random
                self.winners.append(choice)
                surplus = self.votes[choice] - self.win_quota
                print(f"{choice} above threshold, redistributing {surplus} votes")
                self.redistribute_votes(choice, surplus)
                print(self.winners)

            # Error checking case, if less votes than options and all votes have been counted, end with the current choice of options
            elif all(c == 0 for c in self.votes.values()):
                self.winner_count = len(self.winners)
                print(f"No votes remaining, truncating to {self.winner_count} winners.")

            # Otherwise, eliminate lowest voted choice
            else:
                lowest = min(self.choices, key=lambda x: (self.votes[x], self.tie_weights[x], random.random()))   # Pick by votes, then previous round's votes, then random
                print(f"No winners, {lowest} has fewest votes, redistributing {self.votes[lowest]} votes")
                self.redistribute_votes(lowest, self.votes[lowest])
                print(self.winners)


    def redistribute_votes(self, choice, surplus):
        # Remove record for the choice from votes and from possibilities
        self.choices.remove(choice)
        if self.votes[choice] == 0: return
        total_votes = self.votes.pop(choice)
        reassign_ratio = min(surplus / total_votes, 1)  # Calculate weight of each vote

        # Used to record changes to pref to avoid concurrent modification
        remove_pref = []
        adding_pref = Counter()

        # Reassign each group of preferences
        for pref in self.preferences:
            if pref[0] == choice:   # Find preferences for choice
                if len(pref) > 1:   # If pref has second choice
                    count = self.preferences[pref]

                    new_pref = pref[1:]     # Create new run of preferences
                    if new_pref[0] in self.winners:     # If next chosen has already won, skip over them
                        new_pref = new_pref[1:]

                    # Calculate and assign the new amount of votes for the preference
                    new_votes = count * reassign_ratio
                    self.votes[new_pref[0]] += new_votes
                    adding_pref[new_pref] += new_votes

                remove_pref.append(pref)
        # Apply changes
        for p in remove_pref: self.preferences.pop(p)
        for k, v in adding_pref.items(): self.preferences[k] += v

        print(self.votes)
        print(self.preferences)


if __name__ == '__main__':
    choices = [i for i in range(6)]

    # preferences = Counter({
    #     # (0,): 4,
    #     # (1, 0): 2,
    #     # (2, 3): 8,
    #     # (2, 4): 4,
    #     # (3,): 1,
    #     # (4,): 1
    #     (1, 3): 1
    # })
    preferences = Counter({(3, 2, 5, 4, 0, 1): 5, (1, 0): 5})


    stv = STV(choices, preferences, 1)
    stv.run()
    print("WINNERS", stv.winners)
