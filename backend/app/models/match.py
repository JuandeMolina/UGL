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
    matchday: int = db.Column(db.Integer, nullable=False)
    date: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    location: str = db.Column(db.String(50), nullable=False)
    cost: float = db.Column(db.Float, nullable=False)
    pda_goals: int = db.Column(db.Integer, default=0)
    atg_goals: int = db.Column(db.Integer, default=0)
    is_completed: bool = db.Column(db.Boolean, default=False)
    playing_now: bool = db.Column(db.Boolean, default=False)
    pda_kit_color: str = db.Column(db.String(20), nullable=True)
    atg_kit_color: str = db.Column(db.String(20), nullable=True)
    mvp_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)

    mvp = db.relationship("Player", foreign_keys=[mvp_id])

    assignments = db.relationship(
        "MatchAssignment", backref="match", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Match {self.id} — {self.date.strftime('%Y-%m-%d')}>"
