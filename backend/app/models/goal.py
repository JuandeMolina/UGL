"""
Module Name: Goal Model
Description: Database Goal table model.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import zoneinfo
from datetime import datetime

from ..core import db


class Goal(db.Model):
    """Represents a goal event in a match."""
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    team = db.Column(db.String(3), nullable=False)
    scoring_player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    assisting_player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    minute = db.Column(db.Integer, nullable=False, default=0)
    
    # Creation time in Spain/Madrid timezone to match kickoff
    created_at = db.Column(db.DateTime, nullable=False)

    match = db.relationship("Match", back_populates="goals")
    scoring_player = db.relationship("Player", foreign_keys=[scoring_player_id])
    assisting_player = db.relationship("Player", foreign_keys=[assisting_player_id])

    def __init__(self, **kwargs):
        super(Goal, self).__init__(**kwargs)
        # Set creation time to Madrid timezone on initialization
        madrid_tz = zoneinfo.ZoneInfo("Europe/Madrid")
        self.created_at = datetime.now(madrid_tz)

    def calculate_minute(self):
        """Calculates the match minute by comparing creation time with kickoff."""
        if not self.match or not self.match.kick_off_actual_time:
            return 0
        
        inicio = self.match.kick_off_actual_time
        ahora = self.created_at
        
        # Ensure both datetimes are timezone-aware for subtraction
        madrid_tz = zoneinfo.ZoneInfo("Europe/Madrid")
        if inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=madrid_tz)
        if ahora.tzinfo is None:
            ahora = ahora.replace(tzinfo=madrid_tz)

        delta = ahora - inicio
        return max(0, int(delta.total_seconds() / 60)) + 1 # Avoid minute 0 goals