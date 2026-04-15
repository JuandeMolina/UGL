"""
Module Name: Player Model
Description:
    Database Player table model.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from ..core import db


class Player(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    is_goalkeeper: bool = db.Column(db.Boolean, default=False)
    photo_url: str = db.Column(db.String(255), nullable=True)
    jersey_number: int = db.Column(db.Integer, nullable=True)
    description: str = db.Column(db.Text, nullable=True)

    assignments = db.relationship(
        "MatchAssignment", back_populates="player", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Player {self.name}>"
