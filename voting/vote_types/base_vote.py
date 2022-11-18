from typing import List, Tuple

from sqlalchemy import func

from models import db_session
from models.votes import UserVote, Vote, VoteChoice, VoteType


class BaseVote:
    def create_vote(
        self,
        title,
        owner_id,
        choices: List[str],
        type=VoteType.basic,
        vote_limit=None,
        seats=None,
    ) -> Tuple[Vote, List[VoteChoice]]:

        new_vote = Vote(
            title=title,
            owner_id=owner_id,
            type=type,
            vote_limit=vote_limit,
            seats=seats,
            ranked_choice=False,
        )
        db_session.add(new_vote)
        db_session.flush()  # Ensure vote id is fetched

        choice_objs = []
        for i, choice in enumerate(choices):
            new_choice = VoteChoice(vote_id=new_vote.id, choice_index=i, choice=choice)
            db_session.add(new_choice)
            choice_objs.append(new_choice)

        return new_vote, choice_objs

    def vote_for(self, vote, user, option):
        if existing_vote := self._get_existing_vote(vote, user, option):
            self._deregister_vote(existing_vote)
            return f"Removed Vote for **{option.choice}**"
        else:
            self._register_vote(vote, user, option)
            return f"Added Vote for **{option.choice}**"

    def _get_existing_vote(self, vote, user, option):
        return (
            db_session.query(UserVote)
            .filter(UserVote.vote_id == vote.id)
            .filter(UserVote.user_id == user.id)
            .filter(UserVote.choice == option.choice_index)
            .one_or_none()
        )

    def _register_vote(self, vote, user, option):
        user_vote = UserVote(
            vote_id=vote.id, user_id=user.id, choice=option.choice_index
        )
        db_session.add(user_vote)
        db_session.commit()

    def _deregister_vote(self, existing_vote):
        db_session.delete(existing_vote)
        db_session.commit()

    def get_votes_for(self, vote):
        counts = (
            db_session.query(VoteChoice, func.count())
            .join(UserVote)
            .filter(VoteChoice.vote_id == vote.id)
            .group_by(VoteChoice)
            .order_by(func.count().desc())
            .all()
        )
        return counts

    def get_votes_for_user(self, vote, user):
        counts = (
            db_session.query(VoteChoice)
            .join(UserVote)
            .filter(VoteChoice.vote_id == vote.id)
            .filter(UserVote.user_id == user.id)
            .all()
        )
        return counts

    def end(self, vote):
        db_session.delete(vote)
        db_session.commit()

    def remove(self, vote):
        raise NotImplemented()


base_vote = BaseVote()
