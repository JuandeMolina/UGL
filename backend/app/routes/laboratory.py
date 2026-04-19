"""
Module Name: Laboratory API
Description: Advanced statistics and cross-queries for the UGL API.
Author: Juande Molina
"""
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from flask import request
from sqlalchemy import or_, and_
from collections import defaultdict

from ..core import db
from ..models import Match, Goal, MatchAssignment, Player
from .stats import get_short_name

ns = Namespace("laboratory", description="Laboratorio de Estadísticas Avanzadas")

@ns.route("/matches-together")
class MatchesTogether(Resource):
    @jwt_required()
    def get(self):
        p1_id = request.args.get("p1", type=int)
        p2_id = request.args.get("p2", type=int)
        
        if not p1_id or not p2_id:
            return {"error": "Missing player IDs"}, 400
            
        # Get matches where p1 played
        p1_matches = {a.match_id: a.team for a in MatchAssignment.query.filter_by(player_id=p1_id).all()}
        # Get matches where p2 played
        p2_assignments = MatchAssignment.query.filter_by(player_id=p2_id).all()
        
        together_match_ids = []
        for a in p2_assignments:
            if a.match_id in p1_matches and a.team == p1_matches[a.match_id]:
                together_match_ids.append(a.match_id)
                
        matches = Match.query.filter(Match.id.in_(together_match_ids), Match.is_completed == True).order_by(Match.date.desc()).all()
        
        return [{
            "id": m.id,
            "matchday": m.matchday,
            "date": m.date.strftime("%Y-%m-%d"),
            "location": m.location,
            "score": f"{m.pda_goals} - {m.atg_goals}",
            "result": "Victoria" if ((m.pda_goals > m.atg_goals and p1_matches[m.id] == "PDA") or (m.atg_goals > m.pda_goals and p1_matches[m.id] == "ATG")) else ("Empate" if m.pda_goals == m.atg_goals else "Derrota")
        } for m in matches]

@ns.route("/connected-goals")
class ConnectedGoals(Resource):
    @jwt_required()
    def get(self):
        p1_id = request.args.get("p1", type=int)
        p2_id = request.args.get("p2", type=int)
        
        if not p1_id or not p2_id:
            return {"error": "Missing player IDs"}, 400
            
        # Goals where p1 scored and p2 assisted OR vice-versa
        goals = Goal.query.filter(
            or_(
                and_(Goal.scoring_player_id == p1_id, Goal.assisting_player_id == p2_id),
                and_(Goal.scoring_player_id == p2_id, Goal.assisting_player_id == p1_id)
            )
        ).all()
        
        players = {p.id: p.name for p in Player.query.all()}
        matches = {m.id: m for m in Match.query.all()}
        
        return [{
            "id": g.id,
            "match_id": g.match_id,
            "matchday": matches[g.match_id].matchday if g.match_id in matches else "??",
            "minute": g.minute,
            "scorer": players.get(g.scoring_player_id, "???"),
            "assister": players.get(g.assisting_player_id, "???"),
            "team": g.team
        } for g in goals]

@ns.route("/head-to-head")
class HeadToHead(Resource):
    @jwt_required()
    def get(self):
        p1_id = request.args.get("p1", type=int)
        p2_id = request.args.get("p2", type=int)
        
        if not p1_id or not p2_id:
            return {"error": "Missing player IDs"}, 400
            
        p1_assignments = {a.match_id: a.team for a in MatchAssignment.query.filter_by(player_id=p1_id).all()}
        p2_assignments = MatchAssignment.query.filter_by(player_id=p2_id).all()
        
        h2h_matches = []
        stats = {"p1_wins": 0, "p2_wins": 0, "draws": 0, "total": 0}
        
        for a in p2_assignments:
            if a.match_id in p1_assignments and a.team != p1_assignments[a.match_id]:
                m = Match.query.get(a.match_id)
                if not m or not m.is_completed: continue
                
                stats["total"] += 1
                winner = "PDA" if m.pda_goals > m.atg_goals else ("ATG" if m.atg_goals > m.pda_goals else "DRAW")
                
                p1_team = p1_assignments[m.id]
                p2_team = a.team
                
                if winner == "DRAW":
                    stats["draws"] += 1
                elif winner == p1_team:
                    stats["p1_wins"] += 1
                else:
                    stats["p2_wins"] += 1
                    
                h2h_matches.append({
                    "id": m.id,
                    "matchday": m.matchday,
                    "date": m.date.strftime("%Y-%m-%d"),
                    "score": f"{m.pda_goals} - {m.atg_goals}",
                    "p1_team": p1_team,
                    "p2_team": p2_team,
                    "winner": "P1" if winner == p1_team else ("P2" if winner == p2_team else "DRAW")
                })
        
        p1 = Player.query.get(p1_id)
        p2 = Player.query.get(p2_id)
        stats["p1_name"] = get_short_name(p1.name) if p1 else "J1"
        stats["p2_name"] = get_short_name(p2.name) if p2 else "J2"
                
        return {
            "summary": stats,
            "matches": h2h_matches
        }

@ns.route("/ideal-partner")
class IdealPartner(Resource):
    @jwt_required()
    def get(self):
        p_id = request.args.get("p", type=int)
        if not p_id:
            return {"error": "Missing player ID"}, 400
            
        # Get all matches for player
        p_assignments = MatchAssignment.query.filter_by(player_id=p_id).all()
        p_match_teams = {a.match_id: a.team for a in p_assignments}
        
        # Teammate stats: {teammate_id: {wins: 0, total: 0}}
        teammate_stats = defaultdict(lambda: {"wins": 0, "total": 0})
        
        # All relevant match IDs
        match_ids = list(p_match_teams.keys())
        all_assignments = MatchAssignment.query.filter(MatchAssignment.match_id.in_(match_ids)).all()
        matches = {m.id: m for m in Match.query.filter(Match.id.in_(match_ids), Match.is_completed == True).all()}
        
        for a in all_assignments:
            if a.match_id not in matches: continue # Skip if not completed
            if a.player_id == p_id: continue # Skip self
            
            # If same team as player
            if a.team == p_match_teams[a.match_id]:
                m = matches[a.match_id]
                teammate_stats[a.player_id]["total"] += 1
                
                winner = "PDA" if m.pda_goals > m.atg_goals else ("ATG" if m.atg_goals > m.pda_goals else "DRAW")
                if winner == a.team:
                    teammate_stats[a.player_id]["wins"] += 1
                    
        # Filter by min 3 matches
        valid_partners = []
        players_names = {p.id: p.name for p in Player.query.all()}
        
        for pid, s in teammate_stats.items():
            if s["total"] >= 3:
                win_rate = s["wins"] / s["total"]
                valid_partners.append({
                    "id": pid,
                    "name": players_names.get(pid, "???"),
                    "wins": s["wins"],
                    "total": s["total"],
                    "win_rate": round(win_rate * 100, 1)
                })
                
        # Sort by win rate desc, then total matches desc
        valid_partners.sort(key=lambda x: (x["win_rate"], x["total"]), reverse=True)
        
        return valid_partners
