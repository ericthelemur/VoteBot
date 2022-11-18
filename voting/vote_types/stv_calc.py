import secrets
from enum import Enum
from fractions import Fraction
from operator import attrgetter, itemgetter
from typing import Dict, List, Set, Tuple

"""
From UWCS/uwcs-vote

STV calculator

Based on procedure as defined in https://prfound.org/resources/reference/reference-meek-rule/
Uses exact ratio arithmetic to prevent need to use epsilon float comparisons.
Uses a secure random generator to split ties randomly. 
Unfortunately this is more likely to trigger than I'd prefer due to the small populations and single seats.
"""


class ElectionError(RuntimeError):
    pass


class States(Enum):
    HOPEFUL = 0
    WITHDRAWN = 1
    ELECTED = 2
    DEFEATED = 3

    def __repr__(self):
        return "<%s: %r>" % (self._name_, self._value_)

    def __str__(self):
        return "%s" % (self._name_)


class Candidate:
    def __init__(self, id_: int):
        self.id = id_
        self.status = States.HOPEFUL
        self.keep_factor: Fraction = Fraction(1)

    def __str__(self):
        return f"{self.id}: {self.status} ({str(self.keep_factor)})"

    def __repr__(self):
        return self.__str__()


class Vote:
    def __init__(self, candidates: Dict[int, Candidate], prefs: Tuple[int]):
        self.prefs = tuple(map(candidates.get, prefs))

    def check(self, candidates: Set[int]):
        if len(self.prefs) != len(set(self.prefs)):
            raise ElectionError(f"Double Vote [{self.prefs}]")
        for i in self.prefs:
            if i not in candidates:
                raise ElectionError(f"Unknown Candidate [{self.prefs}]")

    def __str__(self):
        return "(" + (", ".join(map(lambda x: str(x.id_), self.prefs))) + ")"

    def __repr__(self):
        return "Vote" + self.__str__()


class Election:
    def __init__(self, candidates: Set[int], votes: List[Tuple[int]], seats: int):
        self.candidatedict = {i: Candidate(i) for i in candidates}
        self.candidates = set(self.candidatedict.values())
        self.votes = [Vote(self.candidatedict, i) for i in votes]
        self.seats = seats
        self.rounds = 0
        self.fulllog = []
        print(candidates, votes, seats)
        # Huge initial value
        # (surplus should never be this high in our situation (its more votes than there are people in the world))
        # If this code is still used when population is this high,
        # why the fuck haven't you moved this to a faster language??????
        self.previous_surplus = Fraction(10000000000000000000000000, 1)
        for i in self.votes:
            i.check(self.candidates)

    def withdraw(self, candidates: Set[int]):
        candidates = [self.candidatedict[cand] for cand in candidates]
        for i in candidates:
            i.status = States.WITHDRAWN
            i.keep_factor = Fraction(0)

    def round(self):
        self.rounds += 1
        # B1
        electable = []
        for candidate in self.candidates:
            if candidate.status == States.ELECTED or candidate.status == States.HOPEFUL:
                electable.append(candidate)
        if len(electable) <= self.seats:
            for i in electable:
                i.status = States.ELECTED
            self._report()
            raise StopIteration("Election Finished")

        # B2a
        wastage = Fraction(0)
        scores = {k: Fraction(0) for k in self.candidates}
        for vote in self.votes:
            weight: Fraction = Fraction(1)
            for candidate in vote.prefs:
                delta: Fraction = weight * candidate.keep_factor
                scores[candidate] += delta
                weight -= delta
            wastage += weight

        # Check all votes accounted for
        assert wastage + sum(scores.values()) == len(self.votes)

        # B2b
        quota = Fraction(sum(scores.values()), self.seats + 1)

        # B2c
        elected = False
        for candidate in self.candidates:
            if candidate.status == States.HOPEFUL and scores[candidate] > quota:
                candidate.status = States.ELECTED
                elected = True

        # B2d
        surplus = Fraction(0)
        for candidate in self.candidates:
            if candidate.status == States.ELECTED:
                surplus += scores[candidate] - quota

        # B2e
        if elected:
            self.previous_surplus = surplus
            self._log(scores, wastage)
            return

        if surplus == 0 or surplus >= self.previous_surplus:
            # B3
            sorted_results = sorted(
                filter(lambda x: x[0].status == States.HOPEFUL, scores.items()),
                key=itemgetter(1),
            )
            min_score = sorted_results[0][1]
            eliminated_candidate: Candidate = self._choose(
                list(filter(lambda x: x[1] <= min_score + surplus, sorted_results))
            )
            eliminated_candidate.status = States.DEFEATED
            eliminated_candidate.keep_factor = Fraction(0)
        else:
            # B2f
            for candidate in self.candidates:
                if candidate.status == States.ELECTED:
                    candidate.keep_factor = Fraction(
                        candidate.keep_factor * quota, scores[candidate]
                    )
        self.previous_surplus = surplus
        self._log(scores, wastage)

    def _choose(self, candidates):
        if len(candidates) > 1:
            a = secrets.choice(candidates)[0]
            self._addlog("-Tiebreak-")
            self._addlog(a)
            self._addlog()
        else:
            a = candidates[0][0]
        return a

    def _addlog(self, *args):
        string = " ".join(map(str, args))
        self.fulllog.append(string)
        print(string)

    def _log(self, scores, wastage):
        self._addlog(self.rounds)
        self._addlog("======")
        for i in self.candidates:
            assert isinstance(i, Candidate)
            self._addlog("Candidate:", i.id, i.keep_factor.limit_denominator(1000))
            self._addlog("Status:", str(i.status))
            self._addlog("Votes:", str(scores[i].limit_denominator(1000)))
            self._addlog()
        self._addlog("Wastage:", str(wastage.limit_denominator(1000)))
        self._addlog()

    def _report(self):
        self._addlog("**Election Results**")
        self._addlog()
        self._addlog("ELECTED")
        for i in filter(lambda x: x.status == States.ELECTED, self.candidates):
            self._addlog(" Candidate", i.id)
        self._addlog("DEFEATED")
        for i in filter(lambda x: x.status == States.DEFEATED, self.candidates):
            self._addlog(" Candidate", i.id)
        self._addlog("WITHDRAWN")
        for i in filter(lambda x: x.status == States.WITHDRAWN, self.candidates):
            self._addlog(" Candidate", i.id)
        self._addlog()

    def full_election(self):
        try:
            while True:
                self.round()
        except StopIteration:
            pass

    def winners(self):
        return map(
            attrgetter("id"),
            filter(lambda x: x.status == States.ELECTED, self.candidates),
        )


def fptp_equivalent():
    c = {1, 2}
    v = [(1, 2)] * 9 + [(2, 1)] * 8 + [(2,)] + [(1,)]
    e = Election(c, v, 1)
    e.full_election()


def immediate_majority():
    c = {1, 2, 3, 4}
    v = [(1, 2, 3, 4)] * 9 + [(2, 3, 1, 4)] * 4 + [(3, 1, 4, 2)] * 3 + [(4, 1)] * 2
    e = Election(c, v, 1)
    e.full_election()


def delayed_majority():
    c = {1, 2, 3, 4}
    v = [(4, 2, 1, 3)] * 4 + [(3, 2, 4, 1)] * 4 + [(2, 4, 1, 3)]
    e = Election(c, v, 1)
    e.full_election()


def delayeder_majority():
    c = {1, 2, 3, 4}
    v = [(4, 2, 1, 3)] * 4 + [(3, 2, 4, 1)] * 5 + [(2, 1, 4, 3)] + [(1, 4, 2, 3)]
    e = Election(c, v, 1)
    e.full_election()


def two_available_three():
    c = {1, 2, 3}
    v = [
        (1, 2, 3),
        (1, 3, 2),
        (2,),
        (3, 1),
        (3, 1),
        (1, 2, 3),
        (2,),
        (1, 3, 2),
        (1, 3, 2),
        (1, 3, 2),
        (1, 3, 2),
        (1, 3, 2),
    ]
    e = Election(c, v, 2)
    e.full_election()


def two_available_four():
    c = {1, 2, 3, 4}
    v = (
        [(4, 2, 1, 3)] * 4
        + [(3, 2, 4, 1)] * 5
        + [(2, 1, 4, 3)] * 3
        + [(1, 4, 2, 3)] * 2
    )
    e = Election(c, v, 2)
    e.full_election()


def tiebreaker():
    c = {1, 2, 3, 4}
    v = [(1,), (2,), (3,), (4,)]
    e = Election(c, v, 1)
    e.full_election()


def malformed():
    c = {1, 2}
    v = [(1, 2, 1)] * 10
    e = Election(c, v, 1)
    e.full_election()


def malformed2():
    c = {1, 2, 3}
    v = [(1, 2, 3, 4)] * 10
    e = Election(c, v, 1)
    e.full_election()


if __name__ == "__main__":
    delayed_majority()
