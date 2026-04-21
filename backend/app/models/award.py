"""
Module Name: Award Model
Description: Database model for player achievements and awards from past ceremonies.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""
from ..core import db

class PlayerAward(db.Model):
    """Represents an award or achievement earned by a player."""
    __tablename__ = "player_award"
    
    id: int = db.Column(db.Integer, primary_key=True)
    player_id: int = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    title: str = db.Column(db.String(100), nullable=False) # e.g. "Bota de Oro"
    gala: str = db.Column(db.String(50), nullable=True)     # e.g. "2024"
    icon: str = db.Column(db.String(20), nullable=True)     # e.g. "🏆", "⚽", "🧤"
    
    # Relationship
    player = db.relationship("Player", back_populates="awards")

    def __repr__(self):
        return f"<PlayerAward {self.title} for Player {self.player_id}>"
