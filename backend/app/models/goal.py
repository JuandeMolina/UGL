from datetime import datetime
import zoneinfo
from ..core import db

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    team = db.Column(db.String(3), nullable=False)
    scoring_player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    assisting_player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    minute = db.Column(db.Integer, nullable=False, default=0)
    
    # IMPORTANTE: Cambiamos a la hora de España para que coincida con el kickoff
    created_at = db.Column(db.DateTime, nullable=False)

    match = db.relationship("Match", back_populates="goals")
    scoring_player = db.relationship("Player", foreign_keys=[scoring_player_id])
    assisting_player = db.relationship("Player", foreign_keys=[assisting_player_id])

    def __init__(self, **kwargs):
        super(Goal, self).__init__(**kwargs)
        # Seteamos la hora de creación en Madrid al nacer
        madrid_tz = zoneinfo.ZoneInfo("Europe/Madrid")
        self.created_at = datetime.now(madrid_tz)

    def calculate_minute(self):
        """Calcula el minuto comparando dos horas en la misma zona horaria."""
        if not self.match or not self.match.kick_off_actual_time:
            return 0
        
        # El kickoff ya se guarda en hora de Madrid según el paso anterior
        inicio = self.match.kick_off_actual_time
        ahora = self.created_at
        
        # Asegurar que ambos tienen zona horaria para la resta
        if inicio.tzinfo is None:
            madrid_tz = zoneinfo.ZoneInfo("Europe/Madrid")
            inicio = inicio.replace(tzinfo=madrid_tz)
        if ahora.tzinfo is None:
            madrid_tz = zoneinfo.ZoneInfo("Europe/Madrid")
            ahora = ahora.replace(tzinfo=madrid_tz)

        delta = ahora - inicio
        return (max(0, int(delta.total_seconds() / 60)) + 1) # Avoid minute 0 goals