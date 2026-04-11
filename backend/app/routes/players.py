"""
Module Name: Players Namespace
Description:
    Endpoints for player listing and individual player stats.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required

from ..models import Player, MatchAssignment, Match

ns = Namespace("players", description="Jugadores")


@ns.route("/")
class PlayerList(Resource):
    @jwt_required()
    def get(self):
        """Lista todos los jugadores."""
        players = Player.query.order_by(Player.name).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "is_goalkeeper": p.is_goalkeeper,
                "photo_url": p.photo_url,
            }
            for p in players
        ], 200


@ns.route("/<int:player_id>")
class PlayerDetail(Resource):
    @jwt_required()
    def get(self, player_id):
        """Devuelve el perfil y estadísticas de un jugador."""
        player = Player.query.get_or_404(player_id)
        assignments = MatchAssignment.query.filter_by(player_id=player_id).all()

        goals = sum(a.goals for a in assignments)
        assists = sum(a.assists for a in assignments)
        matches_played = len(assignments)
        wins = 0
        losses = 0

        for a in assignments:
            match = Match.query.get(a.match_id)
            if match and match.is_completed:
                if a.team == "A":
                    if match.team_a_goals > match.team_b_goals:
                        wins += 1
                    elif match.team_a_goals < match.team_b_goals:
                        losses += 1
                else:
                    if match.team_b_goals > match.team_a_goals:
                        wins += 1
                    elif match.team_b_goals < match.team_a_goals:
                        losses += 1

        return {
            "id": player.id,
            "name": player.name,
            "is_goalkeeper": player.is_goalkeeper,
            "photo_url": player.photo_url,
            "stats": {
                "goals": goals,
                "assists": assists,
                "matches_played": matches_played,
                "wins": wins,
                "losses": losses,
                "draws": matches_played - wins - losses,
            },
        }, 200
