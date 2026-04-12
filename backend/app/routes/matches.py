"""
Module Name: Matches Namespace
Description:
    Endpoints for match listing, creation, detailed management and results.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import Match, MatchAssignment, Player, User, MatchConfirmation
from ..core import db

ns = Namespace("matches", description="Partidos")

match_model = ns.model(
    "Match",
    {
        "matchday": fields.Integer(required=True, description="Número de jornada"),
        "date": fields.String(required=True, description="Fecha del partido (ISO)"),
        "location": fields.String(required=True, description="Lugar del partido"),
        "cost": fields.Float(description="Coste del partido"),
        "pda_kit_color": fields.String(description="Color camistea PDA"),
        "atg_kit_color": fields.String(description="Color camistea ATG"),
    },
)

assignment_model = ns.model(
    "Assignment",
    {
        "player_id": fields.Integer(required=True, description="ID del jugador"),
        "team": fields.String(required=True, description="'PDA' o 'ATG'"),
    },
)

stats_model = ns.model(
    "StatsUpdate",
    {
        "goals": fields.Integer(description="Goles marcados"),
        "assists": fields.Integer(description="Asistencias realizadas"),
    },
)

confirmation_model = ns.model(
    "Confirmation",
    {
        "will_attend": fields.Boolean(required=True, description="¿Asistirá al partido?"),
    },
)


def sync_match_goals(match):
    """Recalcula los goles totales del partido basados en las asignaciones."""
    match.pda_goals = sum(a.goals for a in match.assignments if a.team == "PDA")
    match.atg_goals = sum(a.goals for a in match.assignments if a.team == "ATG")
    db.session.commit()


@ns.route("/")
class MatchList(Resource):
    @jwt_required()
    def get(self):
        """Lista todos los partidos, orden descendente."""
        matches = Match.query.order_by(Match.date.desc()).all()
        return [
            {
                "id": m.id,
                "matchday": m.matchday,
                "date": m.date.isoformat(),
                "location": m.location,
                "cost": m.cost,
                "pda_goals": m.pda_goals,
                "atg_goals": m.atg_goals,
                "is_completed": m.is_completed,
                "playing_now": m.playing_now,
                "pda_kit_color": m.pda_kit_color,
                "atg_kit_color": m.atg_kit_color,
                "assignment_count": len(m.assignments),
                "mvp_id": m.mvp_id,
                "mvp_name": m.mvp.name if m.mvp else None,
            }
            for m in matches
        ], 200

    @jwt_required()
    @ns.expect(match_model)
    def post(self):
        """Registra un nuevo partido."""
        data = ns.payload
        from datetime import datetime
        match = Match(
            matchday=data["matchday"],
            date=datetime.fromisoformat(data["date"]),
            location=data["location"],
            cost=data.get("cost", 0.0),
            pda_kit_color=data.get("pda_kit_color"),
            atg_kit_color=data.get("atg_kit_color"),
        )
        db.session.add(match)
        db.session.commit()


        try:
            from ..utils.push_utils import notify_all_users
            notify_all_users(
                "⚽ ¡Nueva Jornada disponible!", 
                f"Se ha creado la Jornada {match.matchday} ({match.date.strftime('%d/%m')}). ¡Entra para confirmar asistencia!",
                f"/matches/{match.id}"
            )
        except Exception as e:
            print(f"Error enviando notificaciones: {e}")

        return {"id": match.id, "date": match.date.isoformat()}, 201


@ns.route("/<int:match_id>")
class MatchDetail(Resource):
    @jwt_required()
    def get(self, match_id):
        """Devuelve el detalle de un partido con sus asignaciones, confirmaciones y lista de espera."""
        match = Match.query.get_or_404(match_id)
        
        assignments = (
            db.session.query(MatchAssignment, Player.name)
            .join(Player, MatchAssignment.player_id == Player.id)
            .filter(MatchAssignment.match_id == match_id)
            .all()
        )

        # IDs de jugadores ya asignados a equipos
        assigned_player_ids = {a.MatchAssignment.player_id for a in assignments}
        
        # Obtener confirmaciones de asistencia
        confirmations = MatchConfirmation.query.filter_by(match_id=match_id, will_attend=True).all()
        
        # Lista de espera: jugadores que confirmaron asistencia pero NO están asignados
        waiting_list = []
        for conf in confirmations:
            if conf.player_id not in assigned_player_ids:
                waiting_list.append({
                    "player_id": conf.player_id,
                    "player_name": conf.player.name
                })
        
        # Confirmación del usuario actual
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        user_confirmation = None
        if user and user.player_id:
            conf = MatchConfirmation.query.filter_by(
                match_id=match_id,
                player_id=user.player_id
            ).first()
            if conf:
                user_confirmation = conf.will_attend

        return {
            "id": match.id,
            "matchday": match.matchday,
            "date": match.date.isoformat(),
            "location": match.location,
            "cost": match.cost,
            "pda_goals": match.pda_goals,
            "atg_goals": match.atg_goals,
            "is_completed": match.is_completed,
            "playing_now": match.playing_now,
            "pda_kit_color": match.pda_kit_color,
            "atg_kit_color": match.atg_kit_color,
            "mvp_id": match.mvp_id,
            "mvp_name": match.mvp.name if match.mvp else None,
            "assignments": [
                {
                    "id": a.MatchAssignment.id,
                    "player_id": a.MatchAssignment.player_id,
                    "player_name": a.name,
                    "team": a.MatchAssignment.team,
                    "goals": a.MatchAssignment.goals,
                    "assists": a.MatchAssignment.assists,
                }
                for a in assignments
            ],
            "waiting_list": waiting_list,
            "user_confirmation": user_confirmation,
        }, 200

    @jwt_required()
    @ns.expect(match_model)
    def put(self, match_id):
        """Actualiza los detalles básicos de un partido."""
        match = Match.query.get_or_404(match_id)
        data = ns.payload
        
        if "matchday" in data:
            match.matchday = data["matchday"]
        if "date" in data:
            from datetime import datetime
            match.date = datetime.fromisoformat(data["date"])
        if "location" in data:
            match.location = data["location"]
        if "cost" in data:
            match.cost = data["cost"]
        if "pda_kit_color" in data:
            match.pda_kit_color = data["pda_kit_color"]
        if "atg_kit_color" in data:
            match.atg_kit_color = data["atg_kit_color"]
        if "playing_now" in data:
            match.playing_now = bool(data["playing_now"])
        if "is_completed" in data:
            match.is_completed = bool(data["is_completed"])
            
        db.session.commit()
        return {"message": "Partido actualizado con éxito."}, 200


@ns.route("/<int:match_id>/confirm")
class MatchConfirmationResource(Resource):
    @jwt_required()
    @ns.expect(confirmation_model)
    def post(self, match_id):
        """Confirmar o cancelar asistencia al partido."""
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.player_id:
            return {"message": "Usuario sin jugador asociado."}, 400
            
        data = ns.payload or {}
        will_attend = data.get("will_attend", False)
        
        # Buscar confirmación existente
        confirmation = MatchConfirmation.query.filter_by(
            match_id=match_id,
            player_id=user.player_id
        ).first()
        
        if confirmation:
            confirmation.will_attend = will_attend
        else:
            confirmation = MatchConfirmation(
                match_id=match_id,
                player_id=user.player_id,
                will_attend=will_attend
            )
            db.session.add(confirmation)
        
        db.session.commit()
        
        return {
            "message": "Asistencia actualizada.",
            "will_attend": will_attend
        }, 200


@ns.route("/<int:match_id>/assignments")
class MatchAssignmentList(Resource):
    @jwt_required()
    @ns.expect(assignment_model)
    def post(self, match_id):
        """Asigna un jugador a un equipo."""
        data = ns.payload
        match = Match.query.get_or_404(match_id)
        existing = MatchAssignment.query.filter_by(match_id=match_id, player_id=data["player_id"]).first()
        if existing:
            return {"message": "Jugador ya asignado."}, 400

        assignment = MatchAssignment(match_id=match_id, player_id=data["player_id"], team=data["team"])
        db.session.add(assignment)
        db.session.commit()
        return {"id": assignment.id}, 201


@ns.route("/<int:match_id>/assignments/<int:assignment_id>")
class MatchAssignmentDetail(Resource):
    @jwt_required()
    @ns.expect(stats_model)
    def put(self, match_id, assignment_id):
        """Actualiza estadísticas de un jugador en el partido."""
        assignment = MatchAssignment.query.filter_by(id=assignment_id, match_id=match_id).first_or_404()
        data = ns.payload
        if "goals" in data:
            old_goals = assignment.goals
            new_goals = data["goals"]
            assignment.goals = new_goals
            
            sync_match_goals(assignment.match)

            if new_goals > old_goals:
                from ..utils.push_utils import notify_all_users
                notify_all_users(
                    "¡GOOOL!", 
                    f"{assignment.player.name} ha marcado para {assignment.team}. PDA {assignment.match.pda_goals} - {assignment.match.atg_goals} ATG",
                    f"/matches/{match_id}"
                )
        if "assists" in data:
            assignment.assists = data["assists"]
        db.session.commit()
        return {"message": "Estadísticas actualizadas."}, 200

    @jwt_required()
    def delete(self, match_id, assignment_id):
        """Elimina la asignación de un jugador."""
        assignment = MatchAssignment.query.filter_by(id=assignment_id, match_id=match_id).first_or_404()
        match = assignment.match
        db.session.delete(assignment)
        sync_match_goals(match)
        return {"message": "Asignación eliminada."}, 200


@ns.route("/<int:match_id>/complete")
class MatchComplete(Resource):
    @jwt_required()
    def post(self, match_id):
        """Finaliza el partido y calcula el resultado final."""
        match = Match.query.get_or_404(match_id)
        if match.is_completed:
            return {"message": "El partido ya está finalizado."}, 400

        data = ns.payload or {}
        mvp_id = data.get("mvp_id")
        if mvp_id:
            match.mvp_id = mvp_id

        assignments = MatchAssignment.query.filter_by(match_id=match_id).all()
        pda_goals = sum(a.goals for a in assignments if a.team == "PDA")
        atg_goals = sum(a.goals for a in assignments if a.team == "ATG")

        match.pda_goals = pda_goals
        match.atg_goals = atg_goals
        match.is_completed = True
        match.playing_now = False
        
        db.session.commit()
        return {
            "message": "Partido finalizado con éxito.",
            "pda_goals": pda_goals,
            "atg_goals": atg_goals
        }, 200