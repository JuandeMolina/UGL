"""
Module Name: Players Namespace
Description: Endpoints for listing players and retrieving detailed individual statistics.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource, fields

from ..core import db
from ..models import Match, MatchAssignment, Player, PlayerAward

ns = Namespace("players", description="Jugadores")

award_model = ns.model("Award", {
    "title": fields.String(required=True, description="Nombre del premio"),
    "icon": fields.String(description="Emoji representante"),
    "gala": fields.String(description="Año de la gala")
})


@ns.route("/")
class PlayerList(Resource):
    @jwt_required()
    def get(self):
        """Lists all players with advanced performance statistics."""
        players = Player.query.order_by(Player.name).all()

        # Get data from completed matches
        completed_matches = db.session.query(Match).filter(Match.is_completed == True).all()
        match_ids = [m.id for m in completed_matches]
        assignments = db.session.query(MatchAssignment).filter(MatchAssignment.match_id.in_(match_ids)).all() if match_ids else []

        # Initial stats map
        stats_map = {
            p.id: {
                "goals": 0,
                "assists": 0,
                "wins": 0,
                "matches_played": 0,
                "mvp_count": 0,
                "goals_conceded": 0 if p.is_goalkeeper else None
            }
            for p in players
        }

        # Count MVPs
        for m in completed_matches:
            if m.mvp_id and m.mvp_id in stats_map:
                stats_map[m.mvp_id]["mvp_count"] += 1

        # Process assignments
        match_map = {m.id: m for m in completed_matches}
        for a in assignments:
            pid = a.player_id
            if pid not in stats_map:
                continue
            
            stats_map[pid]["matches_played"] += 1
            stats_map[pid]["goals"] += a.goals
            stats_map[pid]["assists"] += a.assists
            
            m = match_map.get(a.match_id)
            if not m:
                continue

            # Win count
            if a.team == "PDA" and m.pda_goals > m.atg_goals:
                stats_map[pid]["wins"] += 1
            elif a.team == "ATG" and m.atg_goals > m.pda_goals:
                stats_map[pid]["wins"] += 1

            # Goals conceded (goalkeepers only)
            p = next((p for p in players if p.id == pid), None)
            if p and p.is_goalkeeper:
                if a.team == "PDA":
                    stats_map[pid]["goals_conceded"] += m.atg_goals
                elif a.team == "ATG":
                    stats_map[pid]["goals_conceded"] += m.pda_goals

        result = []
        for p in players:
            s = stats_map[p.id]
            mp = s["matches_played"]
            
            # Derived metrics
            goals_per_match = round(s["goals"] / mp, 2) if mp > 0 else 0.0
            ga_per_match = round((s["goals"] + s["assists"]) / mp, 2) if mp > 0 else 0.0
            win_pct = round((s["wins"] / mp) * 100, 1) if mp > 0 else 0.0

            result.append({
                "id": p.id,
                "name": p.name,
                "is_goalkeeper": p.is_goalkeeper,
                "position_label": "Portero" if p.is_goalkeeper else "Jugador",
                "photo_url": p.photo_url,
                "jersey_number": p.jersey_number,
                "description": p.description,
                "stats": {
                    **s,
                    "goals_per_match": goals_per_match,
                    "ga_per_match": ga_per_match,
                    "win_percentage": win_pct
                }
            })

        return result, 200


@ns.route("/<int:player_id>")
class PlayerDetail(Resource):
    @jwt_required()
    def get(self, player_id):
        """Returns the profile and detailed statistics for a specific player."""
        player = Player.query.get_or_404(player_id)
        
        # Statistics logic filtered for this player
        completed_matches = db.session.query(Match).filter(Match.is_completed == True).all()
        assignments = MatchAssignment.query.filter_by(player_id=player_id).all()
        
        # Filter assignments for completed matches only
        completed_match_ids = {m.id for m in completed_matches}
        comp_assignments = [a for a in assignments if a.match_id in completed_match_ids]

        goals = sum(a.goals for a in comp_assignments)
        assists = sum(a.assists for a in comp_assignments)
        matches_played = len(comp_assignments)
        wins = 0
        losses = 0
        goals_conceded = 0 if player.is_goalkeeper else None
        
        match_map = {m.id: m for m in completed_matches}
        for a in comp_assignments:
            m = match_map.get(a.match_id)
            if not m: continue
            
            if a.team == "PDA":
                if m.pda_goals > m.atg_goals: wins += 1
                elif m.pda_goals < m.atg_goals: losses += 1
                if player.is_goalkeeper: goals_conceded += m.atg_goals
            elif a.team == "ATG":
                if m.atg_goals > m.pda_goals: wins += 1
                elif m.atg_goals < m.pda_goals: losses += 1
                if player.is_goalkeeper: goals_conceded += m.pda_goals

        mvp_count = Match.query.filter_by(mvp_id=player_id, is_completed=True).count()

        return {
            "id": player.id,
            "name": player.name,
            "is_goalkeeper": player.is_goalkeeper,
            "photo_url": player.photo_url,
            "jersey_number": player.jersey_number,
            "description": player.description,
            "stats": {
                "goals": goals,
                "assists": assists,
                "matches_played": matches_played,
                "wins": wins,
                "losses": losses,
                "draws": matches_played - wins - losses,
                "mvp_count": mvp_count,
                "goals_conceded": goals_conceded,
                "goals_per_match": round(goals / matches_played, 2) if matches_played > 0 else 0.0,
                "ga_per_match": round((goals + assists) / matches_played, 2) if matches_played > 0 else 0.0,
                "win_percentage": round((wins / matches_played) * 100, 1) if matches_played > 0 else 0.0,
            },
            "awards": [
                {
                    "id": a.id,
                    "title": a.title,
                    "icon": a.icon,
                    "gala": a.gala
                } for a in player.awards
            ]
        }, 200

    @jwt_required()
    def put(self, player_id):
        """Updates a player's profile (Admin only)."""
        player = Player.query.get_or_404(player_id)
        data = ns.payload
        
        if "jersey_number" in data:
            player.jersey_number = data["jersey_number"]
        if "description" in data:
            player.description = data["description"]
        if "photo_url" in data:
            player.photo_url = data["photo_url"]
            
        db.session.commit()
        return {"message": "Perfil actualizado correctamente."}, 200

@ns.route("/<int:player_id>/awards")
class AwardList(Resource):
    @jwt_required()
    @ns.expect(award_model)
    def post(self, player_id):
        """Adds a new award to a player (Admin only)."""
        player = Player.query.get_or_404(player_id)
        data = ns.payload
        
        award = PlayerAward(
            player_id=player_id,
            title=data.get("title"),
            icon=data.get("icon", "🏆"),
            gala=data.get("gala")
        )
        db.session.add(award)
        db.session.commit()
        return {"id": award.id}, 201

@ns.route("/awards/<int:award_id>")
class AwardDetail(Resource):
    @jwt_required()
    def delete(self, award_id):
        """Removes an award (Admin only)."""
        award = PlayerAward.query.get_or_404(award_id)
        db.session.delete(award)
        db.session.commit()
        return {"message": "Premio eliminado correctamente."}, 200
