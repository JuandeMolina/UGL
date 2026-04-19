"""
Module Name: MatchAssignment Model
Description: Database MatchAssignment table model. Tracks players, teams, and individual stats per match.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from ..core import db


class MatchAssignment(db.Model):
    """Represents a player's participation in a specific match."""
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    team = db.Column(db.String(3), nullable=False)  # 'PDA' or 'ATG'
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)

    # Relationships
    player = db.relationship("Player", back_populates="assignments")
    match = db.relationship("Match", back_populates="assignments")