"""
Module Name: Matches Namespace
Description: Endpoints for match listing, creation, detailed management, and results.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from ..core import db
from ..models import Match, MatchAssignment, MatchConfirmation, Player, User

ns = Namespace("matches", description="Gestión de Partidos")

match_model = ns.model(
    "Match",
    {
        "matchday": fields.Integer(required=True, description="Número de jornada"),
        "date": fields.String(required=True, description="Fecha del partido (ISO)"),
        "location": fields.String(required=True, description="Lugar del partido"),
        "cost": fields.Float(description="Coste del partido"),
        "pda_kit_color": fields.String(description="Color equipación PDA"),
        "atg_kit_color": fields.String(description="Color equipación ATG"),
    },
)

assignment_model = ns.model(
    "Assignment",
    {
        "player_id": fields.Integer(required=True, description="ID del jugador"),
        "team": fields.String(required=True, description="'PDA' or 'ATG'"),
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

kickoff_model = ns.model(
    "Kickoff",
    {
        "actual_time": fields.String(description="ISO string of the actual start time")
    }
)

goal_post_model = ns.model(
    "GoalPost",
    {
        "team": fields.String(required=True, description="'PDA' or 'ATG'"),
        "scoring_player_id": fields.Integer(description="Scorer player ID (null if own goal)"),
        "assisting_player_id": fields.Integer(description="Assister player ID"),
        "minute": fields.Integer(description="Manual minute (optional)")
    }
)

def sync_match_goals(match):
    """
    Synchronizes the match score and individual player stats with the Goal table.
    """
    from ..models.goal import Goal
    
    # Ensure pending changes are prepared
    db.session.flush()
    
    # Get actual goals from database
    all_goals = Goal.query.filter_by(match_id=match.id).all()
    
    # Global score
    match.pda_goals = len([g for g in all_goals if g.team == "PDA"])
    match.atg_goals = len([g for g in all_goals if g.team == "ATG"])
    
    # Individual stats
    for a in match.assignments:
        a.goals = len([g for g in all_goals if g.scoring_player_id and int(g.scoring_player_id) == int(a.player_id)])
        a.assists = len([g for g in all_goals if g.assisting_player_id and int(g.assisting_player_id) == int(a.player_id)])
        db.session.add(a)
    
    db.session.add(match)
    db.session.commit()
    
    # Refresh to avoid stale cache
    db.session.refresh(match)
    for a in match.assignments:
        db.session.refresh(a)

@ns.route("/")
class MatchList(Resource):
    @jwt_required()
    def get(self):
        """List all matches in descending order."""
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
        """Register a new match."""
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
                "⚽ ¡Nueva jornada disponible!", 
                f"Creada la Jornada {match.matchday} ({match.date.strftime('%d/%m')}). ¡Confirma tu asistencia!",
                f"/matches/{match.id}"
            )
        except Exception as e:
            print(f"Error sending notifications: {e}")

        return {"id": match.id, "date": match.date.isoformat()}, 201


@ns.route("/<int:match_id>")
class MatchDetail(Resource):
    @jwt_required()
    def get(self, match_id):
        """Get match details and current associations."""
        match = Match.query.get_or_404(match_id)
        
        # Players already assigned to teams (PDA/ATG)
        assignments = MatchAssignment.query.filter_by(match_id=match_id).all()
        assigned_player_ids = [int(a.player_id) for a in assignments]
        
        # Attendance confirmations (People who said YES)
        confirmations = MatchConfirmation.query.filter_by(match_id=match_id, will_attend=True).all()
        
        # Waiting list: confirmed people without an assigned team yet
        waiting_list = []
        for conf in confirmations:
            if int(conf.player_id) not in assigned_player_ids:
                waiting_list.append({
                    "player_id": conf.player_id,
                    "player_name": conf.player.name if conf.player else "Jugador Desconocido"
                })
        
        # Current user's response
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        user_confirmation = None
        
        if user and user.player_id:
            conf_existente = MatchConfirmation.query.filter_by(
                match_id=match_id,
                player_id=user.player_id
            ).first()
            if conf_existente:
                user_confirmation = conf_existente.will_attend

        return {
            "id": match.id,
            "matchday": match.matchday,
            "date": match.date.isoformat(),
            "kick_off_actual_time": match.kick_off_actual_time.isoformat() if match.kick_off_actual_time else None,
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
                    "id": a.id,
                    "player_id": a.player_id,
                    "player_name": a.player.name if a.player else "N/A",
                    "team": a.team,
                    "goals": a.goals,
                    "assists": a.assists,
                }
                for a in assignments
            ],
            "waiting_list": waiting_list,
            "user_confirmation": user_confirmation,
        }, 200

    @jwt_required()
    @ns.expect(match_model)
    def put(self, match_id):
        """Update basic match details."""
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
        return {"message": "Partido actualizado correctamente."}, 200


@ns.route("/<int:match_id>/confirm")
class MatchConfirmationResource(Resource):
    @jwt_required()
    @ns.expect(confirmation_model)
    def post(self, match_id):
        """Confirm or cancel attendance to the match."""
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return {"message": "Usuario no encontrado."}, 404

        if not user.player_id:
            return {"message": "No puedes apuntarte con una cuenta de invitado.", "error": "guest_account"}, 403
            
        data = ns.payload or {}
        will_attend = data.get("will_attend", False)
        
        # Search for existing confirmation
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
        """Assigns a player to a team."""
        data = ns.payload
        match = Match.query.get_or_404(match_id)
        existing = MatchAssignment.query.filter_by(match_id=match_id, player_id=data["player_id"]).first()
        if existing:
            return {"message": "El jugador ya está asignado."}, 400

        assignment = MatchAssignment(match_id=match_id, player_id=data["player_id"], team=data["team"])
        db.session.add(assignment)
        db.session.commit()
        return {"id": assignment.id}, 201


@ns.route("/<int:match_id>/assignments/<int:assignment_id>")
class MatchAssignmentDetail(Resource):
    @jwt_required()
    @ns.expect(stats_model)
    def put(self, match_id, assignment_id):
        """Update match stats for a player."""
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
                    "¡GOL!", 
                    f"{assignment.player.name} ha marcado para {assignment.team}. PDA {assignment.match.pda_goals} - {assignment.match.atg_goals} ATG",
                    f"/matches/{match_id}"
                )
        if "assists" in data:
            assignment.assists = data["assists"]
        db.session.commit()
        return {"message": "Estadísticas actualizadas correctamente."}, 200

    @jwt_required()
    def delete(self, match_id, assignment_id):
        """Delete a player assignment."""
        assignment = MatchAssignment.query.filter_by(id=assignment_id, match_id=match_id).first_or_404()
        match = assignment.match
        db.session.delete(assignment)
        sync_match_goals(match)
        return {"message": "Asignación eliminada correctamente."}, 200


@ns.route("/<int:match_id>/kickoff")
class MatchKickoff(Resource):
    @jwt_required()
    def post(self, match_id):
        """Starts the match and sets it to 'In Game'."""
        match = Match.query.get_or_404(match_id)
        
        from datetime import datetime
        from zoneinfo import ZoneInfo
        madrid_tz = ZoneInfo("Europe/Madrid")

        match.kick_off_actual_time = datetime.now(madrid_tz)
        match.playing_now = True
        match.is_completed = False
            
        db.session.commit()
        return {
            "message": "¡Partido empezado!", 
            "kick_off": match.kick_off_actual_time.isoformat(),
            "playing_now": True
        }, 200


@ns.route("/<int:match_id>/goals")
class MatchGoalList(Resource):
    @jwt_required()
    def get(self, match_id):
        """List match goal timeline."""
        from ..models.goal import Goal # Local import to avoid circular dependencies
        goals = Goal.query.filter_by(match_id=match_id).order_by(Goal.minute.asc()).all()
        return [{
            "id": g.id,
            "team": g.team,
            "scoring_player": g.scoring_player.name if g.scoring_player else "⭕ Gol en propia",
            "scoring_player_id": g.scoring_player_id,
            "assisting_player": g.assisting_player.name if g.assisting_player else None,
            "assisting_player_id": g.assisting_player_id,
            "minute": g.minute
        } for g in goals], 200

    @jwt_required()
    @ns.expect(goal_post_model)
    def post(self, match_id):
        """Registers a new goal."""
        from ..models.goal import Goal
        match = Match.query.get_or_404(match_id)
        data = ns.payload
        
        # Capture minute from form
        manual_minute = data.get("minute")
        
        new_goal = Goal(
            match=match, 
            team=data["team"],
            scoring_player_id=data.get("scoring_player_id"),
            assisting_player_id=data.get("assisting_player_id")
        )

        if manual_minute is not None:
            new_goal.minute = int(manual_minute)
        else:
            new_goal.minute = new_goal.calculate_minute()
            
        db.session.add(new_goal)
        sync_match_goals(match)
        
        return {"message": "Gol registrado correctamente", "minute": new_goal.minute}, 201


@ns.route("/<int:match_id>/goals/<int:goal_id>")
class MatchGoalDelete(Resource):
    @jwt_required()
    def delete(self, match_id, goal_id):
        """Deletes a goal and recalculates score."""
        from ..models.goal import Goal
        goal = Goal.query.filter_by(id=goal_id, match_id=match_id).first_or_404()
        match = goal.match
        
        db.session.delete(goal)
        db.session.commit()
        
        sync_match_goals(match) 
        return {"message": "Gol eliminado correctamente."}, 200


@ns.route("/<int:match_id>/complete")
class MatchComplete(Resource):
    @jwt_required()
    def post(self, match_id):
        """Finalizes the match and assigns MVP."""
        match = Match.query.get_or_404(match_id)
        if match.is_completed:
            return {"message": "El partido ya está finalizado."}, 400

        data = ns.payload or {}
        mvp_id = data.get("mvp_id")
        if mvp_id:
            match.mvp_id = mvp_id

        # Final synchronization
        sync_match_goals(match)

        # Close match
        match.is_completed = True
        match.playing_now = False
        
        db.session.commit()
        
        return {
            "message": "Partido finalizado correctamente.",
            "pda_goals": match.pda_goals,
            "atg_goals": match.atg_goals
        }, 200