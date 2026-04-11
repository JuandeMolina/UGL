"""
Module Name: MatchAssignment Model
Description:
    Database MatchAssignment table model.
    Tracks which player was in which team for each match,
    and records individual goals and assists.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from ..core import db


class MatchAssignment(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    match_id: int = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    player_id: int = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    team: str = db.Column(db.String(1), nullable=False)  # 'A' o 'B'
    goals: int = db.Column(db.Integer, default=0)
    assists: int = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<MatchAssignment match={self.match_id} player={self.player_id} team={self.team}>"
