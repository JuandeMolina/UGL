"""
Module Name: Matches Namespace
Description:
    Endpoints for match listing, creation and detailed management.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

from ..models import Match, MatchAssignment, Player
from ..core import db

ns = Namespace("matches", description="Partidos")

match_model = ns.model(
    "Match",
    {
        "date": fields.String(required=True, description="Fecha del partido (ISO)"),
    },
)


@ns.route("/")
class MatchList(Resource):
    @jwt_required()
    def get(self):
        """Lista todos los partidos, orden descendente."""
        matches = Match.query.order_by(Match.date.desc()).all()
        return [
            {
                "id": m.id,
                "date": m.date.isoformat(),
                "team_a_goals": m.team_a_goals,
                "team_b_goals": m.team_b_goals,
                "is_completed": m.is_completed,
            }
            for m in matches
        ], 200

    @jwt_required()
    @ns.expect(match_model)
    def post(self):
        """Registra un nuevo partido."""
        data = ns.payload
        from datetime import datetime
        match = Match(date=datetime.fromisoformat(data["date"]))
        db.session.add(match)
        db.session.commit()
        return {"id": match.id, "date": match.date.isoformat()}, 201


@ns.route("/<int:match_id>")
class MatchDetail(Resource):
    @jwt_required()
    def get(self, match_id):
        """Devuelve el detalle de un partido con sus asignaciones."""
        match = Match.query.get_or_404(match_id)
        assignments = MatchAssignment.query.filter_by(match_id=match_id).all()
        return {
            "id": match.id,
            "date": match.date.isoformat(),
            "team_a_goals": match.team_a_goals,
            "team_b_goals": match.team_b_goals,
            "is_completed": match.is_completed,
            "assignments": [
                {
                    "id": a.id,
                    "player_id": a.player_id,
                    "team": a.team,
                    "goals": a.goals,
                    "assists": a.assists,
                }
                for a in assignments
            ],
        }, 200
