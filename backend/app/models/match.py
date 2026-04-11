"""
Module Name: Match Model
Description:
    Database Match table model.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from datetime import datetime

from ..core import db


class Match(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    date: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    team_a_goals: int = db.Column(db.Integer, default=0)
    team_b_goals: int = db.Column(db.Integer, default=0)
    is_completed: bool = db.Column(db.Boolean, default=False)

    assignments = db.relationship(
        "MatchAssignment", backref="match", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Match {self.id} — {self.date.strftime('%Y-%m-%d')}>"
