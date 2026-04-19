"""
Module Name: MatchConfirmation Model
Description: Database MatchConfirmation table model. Tracks player attendance availability for matches.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from ..core import db


class MatchConfirmation(db.Model):
    """Represents a player's attendance confirmation for a specific match."""
    id: int = db.Column(db.Integer, primary_key=True)
    match_id: int = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    player_id: int = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    will_attend: bool = db.Column(db.Boolean, default=False)

    # Relationships
    match = db.relationship("Match", backref="confirmations")
    player = db.relationship("Player", backref="match_confirmations")

    # Constraint: one confirmation per player per match
    __table_args__ = (
        db.UniqueConstraint('match_id', 'player_id', name='unique_match_player_confirmation'),
    )

    def __repr__(self):
        return f"<MatchConfirmation match={self.match_id} player={self.player_id} attending={self.will_attend}>"